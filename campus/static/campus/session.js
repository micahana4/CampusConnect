// Refresh server-rendered account controls when restoring a page from history.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) window.location.reload();
});

// Replace any page supplied by an older service worker's HTML cache.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    window.location.reload();
  }, { once: true });
}
