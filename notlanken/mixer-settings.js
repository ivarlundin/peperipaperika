const STORAGE_KEY = 'notlanken-mixer-v1';

const DEFAULT = {
  masterVol: 72,
  reverb: 8,
  groups: {},
};

export function loadMixerSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT, groups: {} };
    const parsed = JSON.parse(raw);
    return {
      masterVol: clampPct(parsed.masterVol, DEFAULT.masterVol),
      reverb: clampPct(parsed.reverb, DEFAULT.reverb),
      groups: parsed.groups && typeof parsed.groups === 'object' ? parsed.groups : {},
    };
  } catch {
    return { ...DEFAULT, groups: {} };
  }
}

function clampPct(n, fallback) {
  const v = Number(n);
  if (!Number.isFinite(v)) return fallback;
  return Math.max(0, Math.min(100, Math.round(v)));
}

/**
 * @param {import('./audio-engine.js').AudioEngine} engine
 * @param {{ masterVol: HTMLInputElement, reverb: HTMLInputElement, masterVolVal: HTMLElement, reverbVal: HTMLElement }} ui
 */
export function applyMixerSettings(engine, ui) {
  const s = loadMixerSettings();
  ui.masterVol.value = String(s.masterVol);
  ui.masterVolVal.textContent = `${s.masterVol}%`;
  engine.setMasterVolume(s.masterVol / 100);

  ui.reverb.value = String(s.reverb);
  ui.reverbVal.textContent = `${s.reverb}%`;
  engine.setReverbAmount(s.reverb / 100);

  for (const [group, patch] of Object.entries(s.groups)) {
    if (patch && typeof patch === 'object') {
      engine.setGroupMixer(group, patch);
    }
  }
}

/**
 * @param {import('./audio-engine.js').AudioEngine} engine
 * @param {{ masterVol: HTMLInputElement, reverb: HTMLInputElement }} ui
 */
export function saveMixerSettings(engine, ui) {
  const groups = {};
  for (const g of engine.listMixerGroups()) {
    const m = engine.mixer[g];
    groups[g] = { volume: m.volume, mute: m.mute, solo: m.solo };
  }
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      masterVol: Number(ui.masterVol.value),
      reverb: Number(ui.reverb.value),
      groups,
    }),
  );
}
