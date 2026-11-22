import json
from http.client import HTTPException
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def location_search(request):
    if not (request.user.has_perm("campus.add_venue") or request.user.has_perm("campus.change_venue")):
        return JsonResponse({"error": "Sign in with permission to manage venues."}, status=403)

    term = request.GET.get("q", "").strip()
    if not 2 <= len(term) <= 100:
        return JsonResponse({"error": "Enter a city or town name between 2 and 100 characters."}, status=400)

    params = urlencode({"name": term, "count": 5, "language": "en", "format": "json"})
    lookup = Request("https://geocoding-api.open-meteo.com/v1/search?" + params,
                     headers={"Accept": "application/json"})
    try:
        with urlopen(lookup, timeout=5) as response:
            data = json.load(response)
        if not isinstance(data, dict) or not isinstance(data.get("results", []), list) or data.get("error"):
            raise ValueError("Unexpected geocoding response")
        results = []
        for place in data.get("results", [])[:5]:
            lat, lng = place["latitude"], place["longitude"]
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                continue
            parts = dict.fromkeys([place["name"], place.get("admin1"), place.get("country")])
            results.append({"label": ", ".join(filter(None, parts)), "latitude": lat, "longitude": lng})
    except (HTTPException, OSError, TypeError, ValueError, KeyError):
        return JsonResponse({"error": "Place search is unavailable. Choose the location on the map."}, status=503)
    return JsonResponse({"results": results})
