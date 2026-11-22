import json
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from django.test import RequestFactory, SimpleTestCase

from .location_search import location_search


class LocationSearchTests(SimpleTestCase):
    def search(self, term, allowed=True):
        request = RequestFactory().get("/location-search/", {"q": term})
        request.user = Mock()
        request.user.has_perm.side_effect = lambda name: allowed and name == "campus.change_venue"
        return location_search(request)

    @patch("campus.location_search.urlopen")
    def test_returns_map_coordinates_and_localized_name(self, http):
        http.return_value = BytesIO(json.dumps({"results": [{
            "name": "Puerto Princesa", "admin1": "Mimaropa", "country": "Philippines",
            "latitude": 9.74, "longitude": 118.74,
        }]}).encode())
        response = self.search("Puerto Princesa")
        query = parse_qs(urlsplit(http.call_args.args[0].full_url).query)
        self.assertEqual(query["name"], ["Puerto Princesa"])
        self.assertEqual(json.loads(response.content)["results"], [{
            "label": "Puerto Princesa, Mimaropa, Philippines", "latitude": 9.74, "longitude": 118.74,
        }])

    @patch("campus.location_search.urlopen")
    def test_denied_or_short_search_skips_provider(self, http):
        self.assertEqual(self.search("Puerto", allowed=False).status_code, 403)
        self.assertEqual(self.search(" ").status_code, 400)
        http.assert_not_called()

    @patch("campus.location_search.urlopen")
    def test_no_matches_and_outage(self, http):
        http.return_value = BytesIO(b'{"generationtime_ms": 0.1}')
        self.assertEqual(json.loads(self.search("Missing place").content), {"results": []})
        http.side_effect = TimeoutError()
        self.assertEqual(self.search("Puerto").status_code, 503)
