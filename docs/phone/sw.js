// Serves the game pack (wide/, emu/) from this phone's cache, and the page itself when offline.
const PACK = "rotk-pack", SHELL = "rotk-shell-v1";
self.addEventListener("install", (e) => { self.skipWaiting(); });
self.addEventListener("activate", (e) => { e.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  const rel = u.pathname.slice(new URL(self.registration.scope).pathname.length);
  if (/^(wide|emu)\//.test(rel)) {
    e.respondWith(caches.open(PACK).then((c) => c.match(new Request(new URL(rel, self.registration.scope).href), { ignoreSearch: true }))
      .then((r) => r || new Response("not in the game pack: " + rel, { status: 404 })));
    return;
  }
  // The page: newest from the network, the saved copy when offline.
  e.respondWith(fetch(e.request).then((r) => { if (r.ok) { const k = r.clone(); caches.open(SHELL).then((c) => c.put(e.request, k)); } return r; })
    .catch(() => caches.open(SHELL).then((c) => c.match(e.request, { ignoreSearch: true })).then((r) => r || new Response("offline", { status: 503 }))));
});
