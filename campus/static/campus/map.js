(() => {
  const target = document.getElementById("venue-map");
  if (!target) return;
  const status = document.getElementById("map-status");

  if (!window.L) {
    target.hidden = true;
    status.textContent = "The map could not load. Use the venue list below.";
    return;
  }
  const venues = JSON.parse(document.getElementById("venue-data").textContent);
  const map = L.map(target, {scrollWheelZoom: false});
  const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    referrerPolicy: "strict-origin-when-cross-origin",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  tiles.on("tileerror", () => {
    status.textContent = "Some map tiles could not load. You can still open the venue list.";
  });
  const bounds = [];
  for (const venue of venues) {
    const coordinates = [venue.lat, venue.lng];
    bounds.push(coordinates);
    const popup = document.createElement("div");
    const link = document.createElement("a");
    link.href = venue.url;
    link.textContent = venue.name;
    const campus = document.createElement("div");
    campus.textContent = venue.campus;
    const weather = document.createElement("a");
    weather.href = venue.weather;
    weather.textContent = "Venue weather";
    popup.append(link, campus);
    if (venue.landmark) {
      const landmark = document.createElement("div");
      landmark.textContent = venue.landmark;
      popup.append(landmark);
    }
    popup.append(weather);
    if (venue.directions_url) {
      const directions = document.createElement("a");
      directions.href = venue.directions_url;
      directions.textContent = "Get directions";
      popup.append(document.createElement("br"), directions);
    }
    L.marker(coordinates, {title: venue.name, alt: venue.name}).addTo(map).bindPopup(popup);
  }
  map.fitBounds(bounds, {padding: [32, 32], maxZoom: 16});
})();
