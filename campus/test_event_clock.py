from datetime import datetime, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Campus, Category, Event, Organization, Venue


class EventClockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_superuser("editor")
        campus = Campus.objects.create(name="Main", city="Puerto Princesa")
        cls.venue = Venue.objects.create(name="Hall", campus=campus, latitude=9, longitude=118)
        cls.organization = Organization.objects.create(name="Arts", campus=campus)
        cls.category = Category.objects.create(name="Workshop")

    def setUp(self):
        self.client.force_login(self.editor)

    def form_data(self, hour, period):
        return {
            "title": f"Workshop {hour} {period}",
            "venue": self.venue.pk,
            "organization": self.organization.pk,
            "category": self.category.pk,
            "starts_at_0": "2026-12-10",
            "starts_at_1": hour,
            "starts_at_2": "15",
            "starts_at_3": period,
        }

    def test_noon_midnight_and_afternoon(self):
        for hour, period, expected in [("12", "AM", 0), ("12", "PM", 12), ("3", "PM", 15)]:
            with self.subTest(hour=hour, period=period):
                data = self.form_data(hour, period)
                response = self.client.post("/records/events/new/", data)
                self.assertEqual(response.status_code, 302)
                stored = timezone.localtime(Event.objects.get(title=data["title"]).starts_at)
                self.assertEqual(stored.strftime("%Y-%m-%d %H:%M"), f"2026-12-10 {expected:02}:15")

    def test_edit_displays_existing_time_in_manila(self):
        event = Event.objects.create(
            title="Workshop", venue=self.venue, organization=self.organization, category=self.category,
            starts_at=datetime(2026, 12, 9, 19, 15, tzinfo=dt_timezone.utc),
        )
        response = self.client.get(f"/records/events/{event.pk}/edit/")
        self.assertContains(response, "2026-12-10")
        self.assertContains(response, '<option value="3" selected>', html=False)
        self.assertContains(response, '<option value="15" selected>', html=False)
        self.assertContains(response, '<option value="AM" selected>', html=False)

    def test_period_is_required(self):
        data = self.form_data("3", "PM")
        del data["starts_at_3"]
        response = self.client.post("/records/events/new/", data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("starts_at", response.context["form"].errors)
        self.assertFalse(Event.objects.filter(title=data["title"]).exists())
