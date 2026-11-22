(() => {
  const target = document.getElementById("venue-detail-map");
  if (!target) return;

  const status = document.getElementById("venue-detail-map-status");
  const report = message => {
    if (status) status.textContent = message;
  };
  const lat = Number(target.dataset.lat);
  const lng = Number(target.dataset.lng);
  if (!window.L || !target.dataset.lat || !target.dataset.lng ||
      !Number.isFinite(lat) || !Number.isFinite(lng) ||
      Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    target.hidden = true;
    report("The venue map is unavailable. See the location details below.");
    return;
  }

  const map = L.map(target, {scrollWheelZoom: false}).setView([lat, lng], 17);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    referrerPolicy: "strict-origin-when-cross-origin",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).on("tileerror", () => {
    report("Some map tiles could not load. Open the directions link to view the location.");
  }).addTo(map);
  const name = target.dataset.name || "Venue";
  L.marker([lat, lng], {title: name, alt: name}).addTo(map);
})();
