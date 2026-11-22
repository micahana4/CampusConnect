(() => {
  const target = document.getElementById("venue-picker-map");
  if (!target) return;

  const latitude = document.getElementById("id_latitude");
  const longitude = document.getElementById("id_longitude");
  const search = document.getElementById("venue-search-query");
  const button = document.getElementById("venue-search-button");
  const results = document.getElementById("venue-search-results");
  const status = document.getElementById("venue-picker-status");

  if (!window.L) {
    target.hidden = true;
    search.disabled = button.disabled = true;
    status.textContent = "The map could not load. Enter the venue coordinates below.";
    return;
  }

  const map = L.map(target, {scrollWheelZoom: false});
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    referrerPolicy: "strict-origin-when-cross-origin",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map).on("tileerror", () => {
    status.textContent = "Some map tiles could not load. You can also enter the coordinates below.";
  });

  let pin;
  function placePin(point) {
    if (pin) {
      pin.setLatLng(point);
    } else {
      pin = L.marker(point, {draggable: true, title: "Venue location"}).addTo(map);
      pin.on("dragend", () => selectPoint(pin.getLatLng()));
    }
  }

  function selectPoint(point) {
    const {lat, lng} = map.wrapLatLng(point);
    latitude.value = lat.toFixed(5);
    longitude.value = lng.toFixed(5);
    placePin([lat, lng]);
    status.textContent = "Venue location selected. Drag the pin or click the map to move it.";
  }
  map.on("click", event => selectPoint(event.latlng));

  function restorePin() {
    const lat = latitude.valueAsNumber;
    const lng = longitude.valueAsNumber;
    if (Number.isFinite(lat) && Math.abs(lat) <= 90 && Number.isFinite(lng) && Math.abs(lng) <= 180) {
      placePin([lat, lng]);
      map.setView([lat, lng], 17);
    } else {
      if (pin) {
        pin.remove();
        pin = null;
      }
      if (!map.getZoom()) map.setView([9.7763, 118.7342], 13);
    }
  }
  restorePin();
  latitude.addEventListener("change", restorePin);
  longitude.addEventListener("change", restorePin);

  let sequence = 0;
  async function findPlaces() {
    const current = ++sequence;
    const q = search.value.trim();
    results.replaceChildren();
    if (q.length < 2) {
      status.textContent = "Enter at least two characters to find a city or town.";
      return;
    }
    status.textContent = "Searching for places…";
    try {
      const response = await fetch("/location-search/?" + new URLSearchParams({q}), {
        headers: {Accept: "application/json"},
      });
      if (!response.ok) throw new Error("Search unavailable");
      const data = await response.json();
      if (current !== sequence) return;
      for (const place of data.results) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "btn btn-outline-secondary btn-sm me-2 mb-2";
        item.textContent = place.label;
        item.addEventListener("click", () => {
          map.setView([place.latitude, place.longitude], 14);
          status.textContent = "Click the exact venue on the map to place its pin.";
        });
        results.appendChild(item);
      }
      status.textContent = data.results.length
        ? "Choose a place to view it on the map."
        : "No places found. Try a nearby city or town, or zoom in on the map.";
    } catch {
      if (current === sequence)
        status.textContent = "Place search is unavailable. Zoom in and click the venue on the map.";
    }
  }

  button.addEventListener("click", event => {
    event.preventDefault();
    findPlaces();
  });
  search.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      findPlaces();
    }
  });
})();
