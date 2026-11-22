import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from .models import Campus, Venue
from .weather import fetch_forecast


class ForecastTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    @patch("campus.weather.urlopen")
    def test_requests_venue_forecast_and_caches_parsed_data(self, http):
        http.return_value = BytesIO(json.dumps({"daily": {
            "time": ["2026-11-23"],
            "temperature_2m_min": [24.5],
            "temperature_2m_max": [30.1],
            "precipitation_probability_max": [0],
        }}).encode())
        coords = (Decimal("9.7614"), Decimal("118.7520"))
        rows = fetch_forecast(*coords)
        self.assertEqual(rows, [{"day": date(2026, 11, 23), "low": 24.5, "high": 30.1, "rain": 0}])
        query = parse_qs(urlsplit(http.call_args.args[0].full_url).query)
        self.assertEqual(query["latitude"], ["9.7614"])
        self.assertEqual(query["longitude"], ["118.7520"])
        self.assertEqual(fetch_forecast(*coords), rows)
        http.assert_called_once()


class WeatherPageTests(TestCase):
    @patch("campus.weather.urlopen", side_effect=URLError("offline"))
    def test_weather_page_survives_an_outage(self, http):
        campus = Campus.objects.create(name="Main", city="Puerto Princesa")
        venue = Venue.objects.create(campus=campus, name="Field", latitude=9, longitude=118)
        self.assertContains(
            self.client.get("/weather/", {"venue": venue.pk}),
            "forecast is temporarily unavailable",
        )
        http.assert_called_once()

    @patch("campus.weather.urlopen")
    def test_empty_venue_list_skips_the_api(self, http):
        self.assertContains(self.client.get("/weather/"), "Add a venue")
        http.assert_not_called()
