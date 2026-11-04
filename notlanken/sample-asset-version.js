import { allSampleRelPaths } from './sample-manifest.js';

/** Bump when sample bytes or precache set changes (SW + Cache API). */
export const SAMPLE_ASSET_CACHE_NAME = 'notlanken-assets-v3';
export const SAMPLE_URL_VERSION = 'light-opus-1';
export const PRECACHE_REL_PATHS = allSampleRelPaths();
