from __future__ import annotations

from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static

from backend.apps.common.project_config import get_request_project_context


class WebAppManifestView:
    """Controller for the installable web-app manifest."""

    def __call__(self, request):
        project = get_request_project_context(request)
        display_name = project.get("display_name") or "Devixa"
        payload = {
            "name": f"{display_name} | آموزش برنامه‌نویسی پروژه‌محور",
            "short_name": display_name,
            "description": "دوره‌ها، نقشه‌راه‌ها و آموزش پروژه‌محور برنامه‌نویسی.",
            "id": "/",
            "start_url": "/?source=pwa",
            "scope": "/",
            "display": "standalone",
            "orientation": "portrait-primary",
            "lang": "fa",
            "dir": "rtl",
            "background_color": "#070b14",
            "theme_color": "#4f7cff",
            "icons": [
                {
                    "src": static("app/assets/images/brand/devixa-logo-192.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": static("app/assets/images/brand/devixa-logo-512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
        response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
        response["Content-Type"] = "application/manifest+json; charset=utf-8"
        response["Cache-Control"] = "public, max-age=3600"
        return response


class ServiceWorkerView:
    """Serve a root-scoped service worker with conservative caching."""

    SCRIPT = """
const CACHE_NAME = 'devixa-static-v2';
const STATIC_PREFIX = '/static/';
const OFFLINE_URL = '/static/app/assets/pwa/offline.html';
const PRECACHE_URLS = [OFFLINE_URL];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  if (!url.pathname.startsWith(STATIC_PREFIX)) return;

  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((response) => {
      if (!response.ok || response.type !== 'basic') return response;
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      return response;
    }))
  );
});
""".strip()

    def __call__(self, request):
        response = HttpResponse(self.SCRIPT, content_type="application/javascript; charset=utf-8")
        response["Service-Worker-Allowed"] = "/"
        response["Cache-Control"] = "no-cache"
        return response
