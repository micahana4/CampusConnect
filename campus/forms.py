from datetime import datetime, time

from django import forms
from django.forms import modelform_factory
from django.utils import timezone

from .models import Event


class EventClockWidget(forms.MultiWidget):
    template_name = "campus/event_clock.html"

    def __init__(self, attrs=None):
        super().__init__([
            forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            forms.Select(choices=[("", "Hour")] + [(str(h), str(h)) for h in range(1, 13)]),
            forms.Select(choices=[("", "Minute")] + [(f"{m:02}", f"{m:02}") for m in range(60)]),
            forms.Select(choices=[("", "AM/PM"), ("AM", "AM"), ("PM", "PM")]),
        ], attrs)

    def decompress(self, value):
        if not value:
            return [None, None, None, None]
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return [value.date(), str(value.hour % 12 or 12), f"{value.minute:02}",
                "PM" if value.hour >= 12 else "AM"]


class EventClockField(forms.MultiValueField):
    widget = EventClockWidget

    def __init__(self, **kwargs):
        super().__init__(fields=[
            forms.DateField(input_formats=["%Y-%m-%d"]),
            forms.IntegerField(min_value=1, max_value=12),
            forms.IntegerField(min_value=0, max_value=59),
            forms.ChoiceField(choices=[("AM", "AM"), ("PM", "PM")]),
        ], **kwargs)

    def compress(self, values):
        if not values:
            return None
        day, hour, minute, period = values
        hour = hour % 12 + (12 if period == "PM" else 0)
        return timezone.make_aware(datetime.combine(day, time(hour, minute)))


class EventForm(forms.ModelForm):
    starts_at = EventClockField(label="Starts at (Philippine time)")

    class Meta:
        model = Event
        fields = "__all__"

    def clean_starts_at(self):
        selected = self.cleaned_data["starts_at"]
        previous = self.instance.starts_at
        if previous and timezone.localtime(previous).replace(second=0, microsecond=0) == selected:
            return previous
        return selected


def record_form(model):
    if model is Event:
        return EventForm
    return modelform_factory(model, fields="__all__")
