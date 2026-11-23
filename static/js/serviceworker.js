const CACHE_NAME = 'projectsite-cache-v5-greeting';

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll([
        '/static/campus/bootstrap.min.css',
        '/static/campus/site.css',
        '/static/campus/navigation.js',
        '/static/campus/session.js',
        '/static/campus/map.js',
      ]);
    }).then(function() { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(names.filter(function(name) {
        return name.startsWith('projectsite-cache-') && name !== CACHE_NAME;
      }).map(function(name) { return caches.delete(name); }));
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e) {
  const url = new URL(e.request.url);
  // Account-dependent HTML and API responses must always come from the server.
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || !url.pathname.startsWith('/static/')) {
    return;
  }
  e.respondWith(
    caches.open(CACHE_NAME).then(function(cache) { return cache.match(e.request); }).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
