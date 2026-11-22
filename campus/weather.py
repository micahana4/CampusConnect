import json
from datetime import date
from http.client import HTTPException
from math import isfinite
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from .models import Venue


FORECAST_API = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast(latitude, longitude):
    key = f"forecast:v1:{latitude}:{longitude}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    fields = ["temperature_2m_min", "temperature_2m_max", "precipitation_probability_max"]
    params = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(fields),
        "forecast_days": 3,
        "timezone": "auto",
        "temperature_unit": "celsius",
    })
    request = Request(f"{FORECAST_API}?{params}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=5) as response:
        daily = json.load(response)["daily"]

    days = []
    for stamp, low, high, rain in zip(daily["time"], *(daily[f] for f in fields), strict=True):
        for value in (low, high, rain):
            if value is not None and (type(value) not in (int, float) or not isfinite(value)):
                raise ValueError("Invalid weather measurement")
        days.append({"day": date.fromisoformat(stamp), "low": low, "high": high, "rain": rain})
    if not days:
        raise ValueError("No forecast dates")
    cache.set(key, days, 900)
    return days


@require_safe
def venue_weather(request):
    venues = Venue.objects.select_related("campus").order_by("name", "pk")
    venue_id = request.GET.get("venue")
    if venue_id:
        if not venue_id.isascii() or not venue_id.isdigit() or len(venue_id) > 18:
            raise Http404("Invalid venue")
        venue = get_object_or_404(venues, pk=int(venue_id))
    else:
        venue = venues.first()

    days = []
    unavailable = False
    if venue:
        try:
            days = fetch_forecast(venue.latitude, venue.longitude)
        except (OSError, HTTPException, ValueError, KeyError, TypeError):
            unavailable = True
    return render(request, "campus/weather.html", {
        "venues": venues, "venue": venue, "days": days, "unavailable": unavailable,
    })
