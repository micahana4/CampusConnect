from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Campus, Category, Event, Organization, Registration, Student, Venue


class LabWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = get_user_model().objects.create_superuser("coordinator")
        cls.token = Token.objects.create(user=cls.manager)
        call_command("seed_demo", verbosity=0)

    def records(self):
        event = Event.objects.first()
        return [
            ("campuses", Campus, {"name": "Harbor Campus", "city": "Taytay"}, {"city": "Roxas"}),
            ("categories", Category, {"name": "Music"}, {"name": "Theatre"}),
            ("organizations", Organization, {"name": "Choir", "campus": event.venue.campus_id}, {"name": "Band"}),
            ("venues", Venue, {"name": "Library", "campus": event.venue.campus_id, "latitude": "9.70500", "longitude": "118.70100"}, {"latitude": "9.70600"}),
            ("students", Student, {"student_number": "DEMO-007", "first_name": "Sam", "last_name": "Rivera", "campus": event.venue.campus_id}, {"first_name": "Dani"}),
            ("events", Event, {"title": "Lab showcase", "venue": event.venue_id, "category": event.category_id, "organization": event.organization_id, "starts_at": "2028-01-12T10:00"}, {"title": "Open lab"}),
        ]

    def all_records(self):
        data = self.records()
        student = Student.objects.create(campus=Campus.objects.first(), student_number="DEMO-008", first_name="Jo", last_name="Reyes")
        events = list(Event.objects.order_by("pk"))
        return data + [("registrations", Registration, {"student": student.pk, "event": events[0].pk}, {"event": events[1].pk})]

    def test_rest_crud_for_every_table(self):
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        for slug, model, fields, changes in self.all_records():
            with self.subTest(table=slug):
                url = f"/api/{slug}/"
                self.assertEqual(api.get(url).status_code, 200)
                created = api.post(url, fields, format="json")
                self.assertEqual(created.status_code, 201, created.data)
                detail = f"{url}{created.data['id']}/"
                self.assertEqual(api.get(detail).status_code, 200)
                self.assertEqual(api.put(detail, fields, format="json").status_code, 200)
                updated = api.patch(detail, changes, format="json")
                self.assertEqual(updated.status_code, 200, updated.data)
                self.assertEqual(updated.data[next(iter(changes))], next(iter(changes.values())))
                self.assertEqual(api.delete(detail).status_code, 204)
                self.assertEqual(api.get(detail).status_code, 404)

    def test_browser_crud_for_every_table(self):
        self.client.force_login(self.manager)
        for slug, model, fields, changes in self.all_records():
            with self.subTest(table=slug):
                url = f"/records/{slug}/"
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertEqual(self.client.get(url + "new/").status_code, 200)
                if model is Event:
                    fields = {key: value for key, value in fields.items() if key != "starts_at"}
                    fields.update(starts_at_0="2028-01-12", starts_at_1="10",
                                  starts_at_2="00", starts_at_3="AM")
                created = self.client.post(url + "new/", fields)
                self.assertEqual(created.status_code, 302)
                obj = model.objects.latest("pk")
                detail = f"{url}{obj.pk}/"
                self.assertEqual(self.client.get(detail).status_code, 200)
                self.assertEqual(self.client.post(detail+"edit/", {**fields, **changes}).status_code, 302)
                self.assertEqual(self.client.post(detail+"delete/").status_code, 302)
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_registration_choices_distinguish_events_with_the_same_title(self):
        morning = Event.objects.get(title="Student Map Lab")
        afternoon = Event.objects.get(title="Campus Garden Walk")
        Event.objects.filter(pk=morning.pk).update(title="Campus Workshop", starts_at="2026-11-25T01:00:00Z")
        Event.objects.filter(pk=afternoon.pk).update(title="Campus Workshop", starts_at="2026-11-26T07:30:00Z")
        expected_options = {
            morning.pk: f"Campus Workshop — Nov 25, 2026, 9:00 AM — Learning Commons (Bayview Campus) · #{morning.pk}",
            afternoon.pk: f"Campus Workshop — Nov 26, 2026, 3:30 PM — Garden Court (Bayview Campus) · #{afternoon.pk}",
        }
        self.client.force_login(self.manager)
        website = reverse("campus:record_create", args=["registrations"])
        for url in (website, reverse("admin:campus_registration_add"), "/api/registrations/"):
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_ACCEPT="text/html")
                for pk, label in expected_options.items():
                    self.assertContains(response, f'<option value="{pk}">{label}</option>', html=True)

        student = Student.objects.get(student_number="LAB-001")
        response = self.client.post(website, {"event": afternoon.pk, "student": student.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Registration.objects.filter(event=afternoon, student=student).exists())

    def test_upcoming_counter_opens_filtered_directory(self):
        starting = Event.objects.get(title="Student Map Lab")
        past = Event.objects.get(title="Campus Garden Walk")
        past.starts_at = starting.starts_at - timedelta(days=1)
        past.save(update_fields=["starts_at"])
        all_events = reverse("campus:record_list", args=["events"])
        upcoming = f"{all_events}upcoming/"

        with patch("campus.views.timezone.now", return_value=starting.starts_at):
            home = self.client.get(reverse("campus:dashboard"))
            self.assertContains(home, f'<a href="{upcoming}"><span>1</span> Upcoming events</a>', html=True)
            self.assertContains(home, f'<a href="{all_events}">All events</a>', html=True)
            self.assertContains(self.client.get(all_events), past.title)
            listing = self.client.get(upcoming)
            self.assertContains(listing, starting.title)
            self.assertNotContains(listing, past.title)

    def test_upcoming_search_and_pagination_keep_the_filter(self):
        event = Event.objects.get(title="Student Map Lab")
        Event.objects.bulk_create([
            Event(title=f"Lab session {day}", starts_at=event.starts_at + timedelta(days=day),
                  category=event.category, venue=event.venue, organization=event.organization)
            for day in range(1, 21)
        ])
        upcoming = reverse("campus:upcoming_events")
        first = self.client.get(upcoming, {"q": "Lab"})
        self.assertContains(first, f'<a href="{upcoming}">Clear</a>', html=True)
        self.assertContains(first, '<a href="?q=Lab&amp;page=2">Next</a>', html=True)
        second = self.client.get(upcoming, {"q": "Lab", "page": 2})
        self.assertEqual([item.title for item in second.context["page"]], ["Lab session 20"])

    def test_private_records_and_public_map(self):
        self.assertContains(self.client.get("/"), "Learning Commons")
        for slug in ["students", "registrations"]:
            self.assertEqual(self.client.get(f"/records/{slug}/").status_code, 302)
            self.assertIn(self.client.get(f"/api/{slug}/").status_code, [401, 403])
        self.assertIn(self.client.post("/api/categories/", {"name":"Art"}).status_code, [401, 403])

    def test_api_navigation_returns_to_directory_after_login(self):
        root = reverse("api-root")
        login = reverse("login")
        sign_in_for_api = f"{login}?next={root}"
        home = reverse("campus:dashboard")
        self.assertContains(self.client.get(home), f'<a href="{sign_in_for_api}">API</a>', html=True)
        self.assertContains(self.client.get(sign_in_for_api),
                            f'<input type="hidden" name="next" value="{root}">', html=True)
        self.assertEqual(self.client.get("/api/events/").status_code, 200)

        member = get_user_model().objects.create_user("member", password="campus-demo-password")
        response = self.client.post(login, {"username": member.username, "password": "campus-demo-password",
                                            "next": root}, follow=True)
        self.assertEqual(response.redirect_chain, [(root, 302)])
        self.assertEqual(response.status_code, 200)
        self.assertIn("events", response.json())
        self.assertContains(self.client.get(home), f'<a href="{root}">API</a>', html=True)
        for collection in ("students", "registrations"):
            self.assertEqual(self.client.get(f"/api/{collection}/").status_code, 403)
