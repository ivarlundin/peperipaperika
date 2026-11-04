const CACHE_NAME = 'notlanken-assets-v1';

/** @type {Promise<Cache> | null} */
let cacheReady = null;

function openCache() {
  if (!cacheReady) {
    cacheReady = caches.open(CACHE_NAME);
  }
  return cacheReady;
}

/**
 * Fetch with Cache API persistence (same-origin samples + gm-fallback).
 * @param {string} url
 */
export async function cachedFetch(url) {
  if (typeof caches === 'undefined') {
    return fetch(url);
  }
  try {
    const cache = await openCache();
    const hit = await cache.match(url);
    if (hit) return hit.clone();
    const res = await fetch(url);
    if (res.ok && res.type === 'basic') {
      void cache.put(url, res.clone());
    }
    return res;
  } catch {
    return fetch(url);
  }
}

export { CACHE_NAME };
