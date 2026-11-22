from django.contrib import admin

from .forms import RegistrationForm
from .models import Campus, Category, Event, Organization, Registration, Student, Venue
from .permissions import has_record_permission


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ["name", "city"]
    search_fields = ["name", "city"]


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ["name", "campus", "latitude", "longitude"]
    list_filter = ["campus"]
    search_fields = ["name", "campus__name"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "campus"]
    list_filter = ["campus"]
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_number", "last_name", "first_name", "campus"]
    list_filter = ["campus"]
    search_fields = ["student_number", "last_name", "first_name"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "venue", "organization", "category"]
    list_filter = ["category", "venue__campus"]
    search_fields = ["title"]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    form = RegistrationForm
    list_display = ["event", "student", "registered_at"]
    search_fields = ["event__title", "student__student_number"]
    readonly_fields = ["registered_at"]

    def has_add_permission(self, request):
        return has_record_permission(request.user, Registration, "add")

    def has_change_permission(self, request, obj=None):
        return has_record_permission(request.user, Registration, "change")

    def has_view_permission(self, request, obj=None):
        return has_record_permission(request.user, Registration, "view")
