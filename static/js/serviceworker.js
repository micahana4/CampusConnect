self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('projectsite-cache-v1').then(function(cache) {
      return cache.addAll([
        '/',
        '/static/campus/bootstrap.min.css',
        '/static/campus/site.css',
        '/static/campus/map.js',
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});