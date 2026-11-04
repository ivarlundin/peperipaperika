import {
  SAMPLE_ASSET_CACHE_NAME,
  SAMPLE_URL_VERSION,
  PRECACHE_REL_PATHS,
} from './sample-asset-version.js';

const CACHE_NAME = SAMPLE_ASSET_CACHE_NAME;
const BASE = new URL('./', self.location.href);

function sampleUrl(rel) {
  return new URL(`${rel}?v=${encodeURIComponent(SAMPLE_URL_VERSION)}`, BASE).href;
}

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      await Promise.all(
        PRECACHE_REL_PATHS.map(async (rel) => {
          try {
            const res = await fetch(sampleUrl(rel));
            if (res.ok) await cache.put(sampleUrl(rel), res);
          } catch {
            /* precache best-effort */
          }
        }),
      );
    }),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))),
    ).then(() => self.clients.claim()),
  );
});

function isCacheable(url) {
  if (url.origin !== self.location.origin) return false;
  const p = url.pathname;
  return p.includes('/samples/') || p.includes('/midi/') || p.includes('/vendor/');
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (!isCacheable(url)) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) void cache.put(req, res.clone());
      return res;
    }),
  );
});
