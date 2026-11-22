from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from campus.models import Campus, Category, Event, Organization, Registration, Student, Venue


class Command(BaseCommand):
    help = "Add fictional campus events, venues and signups for the lab demo."

    @transaction.atomic
    def handle(self, *args, **options):
        campus, _ = Campus.objects.get_or_create(
            name="Bayview Campus", defaults={"city": "Puerto Princesa"}
        )
        # Approximate demonstration locations, not navigation coordinates.
        hall, _ = Venue.objects.get_or_create(
            campus=campus, name="Learning Commons",
            defaults={"latitude": "9.77630", "longitude": "118.73420"},
        )
        quad, _ = Venue.objects.get_or_create(
            campus=campus, name="Garden Court",
            defaults={"latitude": "9.77740", "longitude": "118.73510"},
        )
        org, _ = Organization.objects.get_or_create(campus=campus, name="Campus Creators")
        categories = ["Workshop", "Community"]
        first_event = None
        for offset, (name, category_name, venue) in enumerate(zip(
            ["Student Map Lab", "Campus Garden Walk"], categories, [hall, quad]
        ), start=2):
            category, _ = Category.objects.get_or_create(name=category_name)
            event = Event.objects.filter(title=name, venue=venue, organization=org).first()
            if event is None:
                event = Event.objects.create(
                    title=name, venue=venue, organization=org, category=category,
                    starts_at=(timezone.now() + timedelta(days=offset)).replace(second=0, microsecond=0),
                )
            if first_event is None:
                first_event = event
        student, _ = Student.objects.get_or_create(student_number="LAB-001", defaults={
            "first_name": "Alex", "last_name": "Dalisay", "campus": campus,
        })
        Registration.objects.get_or_create(student=student, event=first_event)
        self.stdout.write(self.style.SUCCESS("CampusConnect demo records are ready."))
