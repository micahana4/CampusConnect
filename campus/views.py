from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, models, transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from .forms import record_form
from .models import Campus, Category, Event, Organization, Registration, Student, Venue
from .permissions import has_record_permission


CATALOG = {
    "events": Event,
    "organizations": Organization,
    "venues": Venue,
    "campuses": Campus,
    "categories": Category,
    "students": Student,
    "registrations": Registration,
}
LIST_FIELDS = {
    Campus: ("name", "city"),
    Venue: ("name", "campus", "landmark"),
    Category: ("name",),
    Organization: ("name", "campus"),
    Student: ("student_number", "first_name", "last_name", "campus"),
    Event: ("title", "starts_at", "venue", "organization", "category"),
    Registration: ("event", "student", "registered_at"),
}


def access(request, model, action):
    if has_record_permission(request.user, model, action):
        return None
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    raise PermissionDenied


def get_model(slug):
    try:
        return CATALOG[slug]
    except KeyError:
        raise Http404("Unknown directory.") from None


def context(request, slug):
    model = CATALOG[slug]
    return {
        "slug": slug,
        "label": model._meta.verbose_name,
        "plural": model._meta.verbose_name_plural,
        "may_add": has_record_permission(request.user, model, "add"),
        "may_change": has_record_permission(request.user, model, "change"),
        "may_delete": has_record_permission(request.user, model, "delete"),
    }


def upcoming_events():
    return Event.objects.filter(starts_at__gte=timezone.now())


@require_safe
def dashboard(request):
    upcoming = upcoming_events().select_related("organization", "venue", "category")
    venues = Venue.objects.select_related("campus").order_by("name", "pk")
    markers = [
        {
            "name": venue.name,
            "landmark": venue.landmark,
            "directions_url": venue.directions_url,
            "campus": str(venue.campus),
            "lat": float(venue.latitude),
            "lng": float(venue.longitude),
            "url": reverse("campus:record_detail", args=["venues", venue.pk]),
            "weather": f"/weather/?venue={venue.pk}",
        }
        for venue in venues
    ]
    return render(request, "campus/dashboard.html", {
        "upcoming": upcoming[:6], "markers": markers,
        "group_count": Organization.objects.count(),
        "event_count": upcoming.count(), "venue_count": len(markers),
    })


@require_safe
def record_list(request, slug, upcoming=False):
    model = get_model(slug)
    denied = access(request, model, "view")
    if denied:
        return denied
    fields = LIST_FIELDS[model]
    qs = upcoming_events() if upcoming else model.objects.all()
    qs = qs.select_related()
    if not qs.ordered:
        qs = qs.order_by("pk")
    query = request.GET.get("q", "").strip()
    if query:
        searchable = {
            Campus: ("name", "city"), Venue: ("name", "campus__name"),
            Organization: ("name", "campus__name"), Category: ("name",),
            Student: ("student_number", "first_name", "last_name"),
            Event: ("title", "venue__name", "organization__name", "category__name"),
            Registration: ("student__student_number", "student__last_name", "event__title"),
        }
        condition = models.Q()
        for field in searchable[model]:
            condition |= models.Q(**{f"{field}__icontains": query})
        qs = qs.filter(condition)
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "campus/list.html", {
        **context(request, slug), "q": query, "page": page,
        "directory_name": "upcoming events" if upcoming else model._meta.verbose_name_plural,
        "headers": [model._meta.get_field(f).verbose_name for f in fields],
        "rows": [(obj.pk, [getattr(obj, f) for f in fields]) for obj in page],
    })


@require_safe
def record_detail(request, slug, pk):
    model = get_model(slug)
    denied = access(request, model, "view")
    if denied:
        return denied
    obj = get_object_or_404(model.objects.select_related(), pk=pk)
    return render(request, "campus/detail.html", {
        **context(request, slug), "obj": obj,
        "fields": [(model._meta.get_field(f).verbose_name, getattr(obj, f)) for f in LIST_FIELDS[model]],
    })


@require_http_methods(["GET", "POST"])
def edit_record(request, slug, pk=None):
    model = get_model(slug)
    denied = access(request, model, "change" if pk is not None else "add")
    if denied:
        return denied
    obj = get_object_or_404(model, pk=pk) if pk is not None else None
    form = record_form(model)(request.POST if request.method == "POST" else None, instance=obj)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                saved = form.save()
        except IntegrityError:
            form.add_error(None, "This record conflicts with another change. Check the fields and try again.")
        else:
            messages.success(request, f"{model._meta.verbose_name.capitalize()} saved.")
            if not has_record_permission(request.user, model, "view"):
                return redirect("campus:dashboard")
            return redirect("campus:record_detail", slug=slug, pk=saved.pk)
    return render(request, "campus/form.html", {**context(request, slug), "form": form, "obj": obj})


@require_http_methods(["GET", "POST"])
def delete_record(request, slug, pk):
    model = get_model(slug)
    denied = access(request, model, "delete")
    if denied:
        return denied
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, "Other records still use this entry. Reassign or remove those links first.")
        else:
            messages.success(request, f"{model._meta.verbose_name.capitalize()} deleted.")
            if not has_record_permission(request.user, model, "view"):
                return redirect("campus:dashboard")
            return redirect("campus:record_list", slug=slug)
    return render(request, "campus/delete.html", {**context(request, slug), "obj": obj})
