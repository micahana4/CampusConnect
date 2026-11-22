from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format


class Campus(models.Model):
    name = models.CharField(max_length=120, unique=True)
    city = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "campuses"

    def __str__(self):
        return self.name


class Venue(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="venues")
    name = models.CharField(max_length=120)
    landmark = models.CharField("Landmark or location note", max_length=240, blank=True)

    @property
    def directions_url(self):
        return f"https://www.google.com/maps/dir/?api=1&destination={self.latitude},{self.longitude}"

    latitude = models.DecimalField(max_digits=8, decimal_places=5, validators=[
        MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90")),
    ])
    longitude = models.DecimalField(max_digits=8, decimal_places=5, validators=[
        MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180")),
    ])

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["campus", "name"], name="venue_name_per_campus"),
        ]

    def __str__(self):
        return f"{self.name} ({self.campus})"


class Organization(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="organizations")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["campus", "name"], name="org_name_per_campus"),
        ]

    def __str__(self):
        return f"{self.name} ({self.campus})"


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Student(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="students")
    student_number = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)

    class Meta:
        ordering = ["last_name", "first_name", "pk"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_number})"


class Event(models.Model):
    title = models.CharField(max_length=150)
    starts_at = models.DateTimeField(db_index=True)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="events")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="events")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="events")

    class Meta:
        ordering = ["starts_at", "pk"]

    def __str__(self):
        return self.title

    def registration_label(self):
        local_start = timezone.localtime(self.starts_at)
        schedule = date_format(local_start, "M j, Y, g:i A")
        return f"{self.title} — {schedule} — {self.venue} · #{self.pk}"


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="registrations")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registered_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["event", "student"], name="one_signup_per_event"),
        ]

    def __str__(self):
        return f"{self.student} — {self.event}"
