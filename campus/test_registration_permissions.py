from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Event, Registration


class RegistrationPermissionTests(TestCase):
    list_url = "/api/registrations/"

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        registration = Registration.objects.get()
        cls.registration_pk = registration.pk
        cls.detail_url = f"{cls.list_url}{registration.pk}/"
        cls.original = {"event": registration.event_id, "student": registration.student_id}
        other_event = Event.objects.exclude(pk=registration.event_id).get()
        cls.other = {"event": other_event.pk, "student": registration.student_id}

    def user_with_permissions(self, *codenames, staff=False):
        user = get_user_model().objects.create_user(username="-".join(codenames), is_staff=staff)
        for codename in codenames:
            user.user_permissions.add(Permission.objects.get(
                content_type__app_label="campus", codename=codename,
            ))
        return user

    def client_with_permissions(self, *codenames):
        client = APIClient()
        client.force_authenticate(self.user_with_permissions(*codenames))
        return client

    def test_writes_require_both_registration_and_student_permissions(self):
        for permissions in [("add_registration", "change_registration"), ("view_student",)]:
            with self.subTest(permissions=permissions):
                client = self.client_with_permissions(*permissions)
                self.assertEqual(client.post(self.list_url, self.other, format="json").status_code, 403)
                self.assertEqual(client.put(self.detail_url, self.other, format="json").status_code, 403)
                self.assertEqual(client.patch(self.detail_url, {"event": self.other["event"]}, format="json").status_code, 403)
                self.assertEqual(Registration.objects.get().event_id, self.original["event"])

    def test_edits_and_creation_with_student_access(self):
        editor = self.client_with_permissions("change_registration", "view_student")
        self.assertEqual(editor.put(self.detail_url, self.other, format="json").status_code, 200)
        updated = editor.patch(self.detail_url, {"event": self.original["event"]}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["event"], self.original["event"])
        creator = self.client_with_permissions("add_registration", "view_student")
        self.assertEqual(creator.post(self.list_url, self.other, format="json").status_code, 201)

    def test_read_and_delete_use_their_own_registration_permissions(self):
        reader = self.client_with_permissions("view_registration")
        self.assertEqual(reader.get(self.list_url).status_code, 200)
        self.assertEqual(reader.get(self.detail_url).status_code, 200)
        self.assertEqual(reader.delete(self.detail_url).status_code, 403)
        remover = self.client_with_permissions("delete_registration")
        self.assertEqual(remover.get(self.detail_url).status_code, 403)
        self.assertEqual(remover.delete(self.detail_url).status_code, 204)
        self.assertFalse(Registration.objects.exists())

    def test_website_shows_only_permitted_registration_actions(self):
        listing = reverse("campus:record_list", args=["registrations"])
        detail = reverse("campus:record_detail", args=["registrations", self.registration_pk])
        create = reverse("campus:record_create", args=["registrations"])
        edit = reverse("campus:record_update", args=["registrations", self.registration_pk])
        cases = [
            (("add_registration", "change_registration"), False, False),
            (("view_student", "add_registration"), True, False),
            (("view_student", "change_registration"), False, True),
        ]
        for permissions, may_add, may_edit in cases:
            with self.subTest(permissions=permissions):
                self.client.force_login(self.user_with_permissions("view_registration", *permissions))
                for page, link, allowed in [(listing, create, may_add), (detail, edit, may_edit)]:
                    response = self.client.get(page)
                    if allowed:
                        self.assertContains(response, f'href="{link}"')
                        self.assertContains(self.client.get(link), 'name="student"')
                    else:
                        self.assertNotContains(response, f'href="{link}"')

    def test_admin_registration_reader_gets_a_read_only_form_without_student_access(self):
        user = self.user_with_permissions("view_registration", "add_registration", "change_registration", staff=True)
        self.client.force_login(user)
        create = reverse("admin:campus_registration_add")
        edit = reverse("admin:campus_registration_change", args=[self.registration_pk])
        listing = self.client.get(reverse("admin:campus_registration_changelist"))
        self.assertNotContains(listing, f'href="{create}"')
        self.assertEqual(self.client.get(create).status_code, 403)
        response = self.client.get(edit)
        self.assertNotContains(response, 'name="student"')
        self.assertNotContains(response, 'name="_save"')

    def test_admin_staff_with_student_access_can_change_and_add_registrations(self):
        user = self.user_with_permissions("add_registration", "change_registration", "view_student", staff=True)
        self.client.force_login(user)
        create = reverse("admin:campus_registration_add")
        edit = reverse("admin:campus_registration_change", args=[self.registration_pk])
        self.assertContains(self.client.get(edit), 'name="student"')
        self.assertEqual(self.client.post(edit, self.other).status_code, 302)
        self.assertTrue(Registration.objects.filter(pk=self.registration_pk, **self.other).exists())
        self.assertContains(self.client.get(create), 'name="student"')
        self.assertEqual(self.client.post(create, self.original).status_code, 302)
        self.assertTrue(Registration.objects.filter(**self.original).exists())
