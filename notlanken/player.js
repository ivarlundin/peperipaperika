import { Midi } from './vendor/tonejs-midi.mjs';
import { getAudioEngine, GROUPS } from './audio-engine.js';
import {
  barStarts,
  formatBarBeat,
  formatClock,
  jumpBars,
  secondsToBarBeat,
  songDurationSeconds,
} from './midi-time.js';
import {
  loadNotes,
  noteTypeLabel,
  saveNotes,
} from './session-notes.js';
import { chordAtTime, parseSongMeta } from './midi-meta.js';
import { detectWrittenTracks, missingTracks } from './autokomp-detect.js';
import {
  defaultStyleForMeter,
  generate as generateAutokomp,
  loadStyles,
  parseKompDirectives,
  resolveStyleId,
} from './autokomp.js';
import { createSongLoadGuard } from './song-load-guard.js';
import { applyMixerSettings, saveMixerSettings } from './mixer-settings.js';
import { createLcdTitle } from './lcd-display.js';

const engine = getAudioEngine(new URL('./', import.meta.url).href);
const songLoadGuard = createSongLoadGuard();

const $ = (id) => document.getElementById(id);

const songList = $('song-list');
const songFilter = $('song-filter');
const viewList = $('view-list');
const playerEl = $('player');
const btnBack = $('btn-back');
const btnCopyLink = $('btn-copy-link');
const siteHome = $('site-home');
const nowPlaying = $('now-playing');
const lcdTitle = $('lcd-title');
const lcdTitleDisplay = createLcdTitle(lcdTitle);
const chordLine = $('chord-line');
const btnPlayPause = $('btn-play-pause');
const btnPlayPauseIconPlay = btnPlayPause?.querySelector('.icon-play');
const btnPlayPauseIconPause = btnPlayPause?.querySelector('.icon-pause');
const btnStop = $('btn-stop');
const timeline = $('timeline');
const lane = $('lane');
const laneTrack = $('lane-track');
const lanePinned = $('lane-pinned');
const laneRoll = $('lane-roll');
const timelineRail = $('timeline-rail');
const timelineSections = $('timeline-sections');
const timelineNotes = $('timeline-notes');
const timelinePlayhead = $('timeline-playhead');
const timeBarBeat = $('time-barbeat');
const timeElapsed = $('time-elapsed');
const timeTotal = $('time-total');
const timeElapsedDock = $('time-elapsed-dock');
const timeRemaining = $('time-remaining');
const btnPrev = $('btn-prev');
const btnNext = $('btn-next');
const btnKompQuick = $('btn-komp-quick');
const transportKompKey = $('transport-komp-key');
const speedOptions = $('speed-options');
const reverbSlider = $('reverb');
const reverbVal = $('reverb-val');
const btnMixer = $('btn-mixer');
const mixerPanel = $('mixer-panel');
const mixerGroups = $('mixer-groups');
const masterVol = $('master-vol');
const masterVolVal = $('master-vol-val');
const noteAdd = $('note-add');
const notesList = $('notes-list');
const btnCopyNotes = $('btn-copy-notes');
const btnClearNotes = $('btn-clear-notes');
const statusEl = $('status');
const noteDialog = $('note-dialog');
const noteForm = $('note-form');
const noteText = $('note-text');
const noteDialogMeta = $('note-dialog-meta');
const noteDialogTitle = $('note-dialog-title');
const noteCancel = $('note-cancel');
const kompSwitch = $('komp-switch');
const kompStyle = $('komp-style');
const kompBar = $('komp-bar');
const kompStylePicker = $('komp-style-picker');
const kompStyleTrigger = $('komp-style-trigger');
const kompStyleList = $('komp-style-list');
const btnSpeed = $('btn-speed');
const speedDialog = $('speed-dialog');
const speedClose = $('speed-close');
const mixerDialog = $('mixer-dialog');
const mixerClose = $('mixer-close');

/** @type {{ file: string, title: string } | null} */
let currentSong = null;
/** @type {import('@tonejs/midi').Midi | null} */
let midi = null;
let events = [];
/** @type {{ time: number, label: string }[]} */
let sections = [];
/** @type {{ time: number, symbol: string }[]} */
let chords = [];
let duration = 0;
let position = 0;
let isPlaying = false;
let playStartAc = 0;
let playStartPos = 0;
let raf = 0;
let scrubbing = false;
/** @type {import('./session-notes.js').SessionNote[]} */
let sessionNotes = [];
let pendingNoteType = 'note';
let noteDialogOpen = false;
let writtenEvents = [];
let autoEvents = [];
let writtenTracks = { drums: false, bass: false, piano: false };
let autoGroups = new Set();
let styleCatalog = null;
/** @type {Map<string, object>} */
let styleMap = new Map();
let kompOn = true;
let kompVariantPref = 'auto';
let kompDirectives = { style: null, sectionStyles: new Map() };
let audioBusy = false;
let playbackSeq = 0;

/** @type {string} */
let listHighlightFile = '';
function cancelInFlightPlayback() {
  playbackSeq += 1;
  audioBusy = false;
}

const GROUP_LABELS = {
  piano: 'Piano',
  bass: 'Bas',
  drums: 'Trummor',
  brass: 'Blås',
  other: 'Övrigt',
};

const GROUP_ICONS = {
  piano: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5h16v14H4zm2-2h2v-2H6v2zm0-4h2V9H6v4zm4 4h2v-2h-2v2zm0-4h2V9h-2v4zm4 4h2v-2h-2v2zm0-4h2V9h-2v4z"/></svg>',
  bass: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 18c0-2.5 1.5-4.5 3.5-6L7 6.5 8.5 5l3.5 5.5C14 9 16 8 18 8v2c-1.8 0-3.5.8-4.7 2.1 1.8 1.4 2.7 3.3 2.7 5.9H7z"/></svg>',
  drums: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 10V7h12v3H6zm0 2h12v3H6v-3zm-2 5h16v2H4v-2z"/></svg>',
  brass: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 17c-2.2 0-4-1.3-4.8-3.2L4 12l-.8-1.8C4 8.3 5.8 7 8 7h8c2.2 0 4 1.3 4.8 3.2L20 12l.8 1.8C20 15.7 18.2 17 16 17H8zm0-2h8c1.1 0 2-.6 2.4-1.5L17 12l.4-1.5C17.6 9.6 16.9 9 16 9H8c-1.1 0-2 .6-2.4 1.5L5 12l-.4 1.5C5.4 14.4 6.1 15 8 15z"/></svg>',
  other: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-9 9v7h2v-7a7 7 0 0 1 14 0v7h2v-7a9 9 0 0 0-9-9zm-1 16h2v3h-2z"/></svg>',
};

function setStatus(msg, isError = false) {
  if (isPlayerView() && !isError) {
    statusEl.textContent = '';
    statusEl.classList.remove('error');
    return;
  }
  statusEl.textContent = msg || '';
  statusEl.classList.toggle('error', isError);
  statusEl.classList.toggle('visually-hidden', !msg && !isError);
}

function positionFaderBubble(input, bubble) {
  if (!input || !bubble) return;
  const min = Number(input.min) || 0;
  const max = Number(input.max) || 100;
  const val = Number(input.value);
  const pct = max > min ? (val - min) / (max - min) : 0;
  bubble.style.left = `${pct * 100}%`;
  bubble.textContent = `${Math.round(val)}%`;
}

function bindHorizontalFader(input, bubble, onInput) {
  if (!input) return;
  const show = () => {
    if (bubble) {
      positionFaderBubble(input, bubble);
      bubble.hidden = false;
      input.closest('.mixer-track-row')?.classList.add('is-fader-active');
    }
  };
  const hide = () => {
    if (bubble) bubble.hidden = true;
    input.closest('.mixer-track-row')?.classList.remove('is-fader-active');
  };
  input.addEventListener('input', () => {
    show();
    onInput?.();
  });
  input.addEventListener('pointerdown', show);
  input.addEventListener('pointerup', hide);
  input.addEventListener('pointercancel', hide);
  input.addEventListener('blur', hide);
}

function syncTransportKompKey() {
  if (!transportKompKey || !chords.length) {
    if (transportKompKey) transportKompKey.textContent = '—';
    return;
  }
  const chord = chordAtTime(chords, position);
  transportKompKey.textContent = chord || '—';
}

function copySongLink() {
  if (!currentSong) return;
  const url = new URL(location.href);
  url.hash = encodeURIComponent(currentSong.file);
  navigator.clipboard.writeText(url.href).then(
    () => setStatus('Länk kopierad — dela med arrangör eller band.'),
    () => setStatus('Kunde inte kopiera länk.', true),
  );
}

function isTypingTarget() {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable;
}

function isModuleDialogOpen() {
  return !!(speedDialog?.open || mixerDialog?.open);
}

/** Modal: Esc (native), overlay click, and explicit close control. */
function bindModuleDialog(dialog, trigger, closeBtn) {
  if (!dialog) return;
  const syncExpanded = () => {
    if (trigger) {
      trigger.setAttribute('aria-expanded', String(dialog.open));
      trigger.classList.toggle('is-active', dialog.open);
    }
  };
  dialog.addEventListener('close', syncExpanded);
  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) dialog.close();
  });
  closeBtn?.addEventListener('click', () => dialog.close());
  trigger?.addEventListener('click', () => {
    if (dialog.open) dialog.close();
    else dialog.showModal();
    syncExpanded();
  });
}

/** @type {{ file: string, title: string }[]} */
let songs = [];

function isPlayerView() {
  return !playerEl.hidden;
}

function showListView() {
  songLoadGuard.bump();
  cancelInFlightPlayback();
  stop();
  if (currentSong?.file) listHighlightFile = currentSong.file;
  currentSong = null;
  midi = null;
  playerEl.hidden = true;
  viewList.hidden = false;
  document.title = 'Notlänken ™';
  renderSongList(songFilter?.value || '');
  updateAutokompUi();
  songFilter?.focus({ preventScroll: true });
}

function showPlayerView() {
  viewList.hidden = true;
  playerEl.hidden = false;
  window.scrollTo(0, 0);
}

function routeFromHash() {
  const file = decodeURIComponent(location.hash.replace(/^#/, ''));
  const song = file ? songs.find((s) => s.file === file) : null;
  if (!song) {
    if (isPlayerView()) showListView();
    return;
  }
  if (currentSong?.file === song.file && isPlayerView()) return;
  openSong(song);
}

function renderSongList(filter = '') {
  const q = filter.trim().toLowerCase();
  songList.innerHTML = '';
  const visible = q
    ? songs.filter((s) => s.title.toLowerCase().includes(q) || s.file.toLowerCase().includes(q))
    : songs;
  if (!visible.length) {
    const li = document.createElement('li');
    li.className = 'song-empty';
    li.textContent = q ? 'Inga träffar – prova ett annat sökord.' : 'Inga låtar i listan.';
    songList.appendChild(li);
    return;
  }
  for (const song of visible) {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'song-btn';
    const title = document.createElement('span');
    title.className = 'song-btn-title';
    title.textContent = song.title;
    btn.appendChild(title);
    btn.addEventListener('click', () => {
      engine.ensureContext();
      location.hash = encodeURIComponent(song.file);
    });
    const markerFile = isPlayerView() ? currentSong?.file : listHighlightFile;
    if (markerFile && markerFile === song.file) {
      btn.setAttribute('aria-current', 'true');
    }
    li.appendChild(btn);
    songList.appendChild(li);
  }
}

async function loadManifest() {
  const res = await fetch('midi/songs.json');
  songs = await res.json();
  renderSongList(songFilter?.value || '');
  routeFromHash();
}

if (songFilter) {
  songFilter.addEventListener('input', () => renderSongList(songFilter.value));
}


async function openSong(song) {
  await kompReady;
  const loadToken = songLoadGuard.bump();
  cancelInFlightPlayback();
  audioBusy = true;
  engine.stopAll();
  isPlaying = false;
  cancelAnimationFrame(raf);

  midi = null;
  currentSong = song;
  listHighlightFile = song.file;
  document.title = `${song.title} – Notlänken ™`;
  nowPlaying.textContent = song.title;
  lcdTitleDisplay.setText(song.title);
  showPlayerView();
  updateTransportUi();
  setStatus('Laddar MIDI…');

  try {
    const res = await fetch(`midi/${encodeURIComponent(song.file)}`);
    if (!songLoadGuard.isActive(loadToken)) return;
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const buf = await res.arrayBuffer();
    if (!songLoadGuard.isActive(loadToken)) return;

    const loadMidi = new Midi(buf);
    const loadWrittenEvents = engine.buildEvents(loadMidi);
    const loadWrittenTracks = detectWrittenTracks(loadMidi);
    const meta = parseSongMeta(loadMidi);
    const loadSections = meta.sections;
    const loadChords = meta.chords;
    const loadDuration = songDurationSeconds(loadMidi, {
      writtenEvents: loadWrittenEvents,
      chords: loadChords,
      sections: loadSections,
    });

    const loadKompDirectives = parseKompDirectives(loadMidi);
    let loadEvents = loadWrittenEvents;
    if (kompOn && loadChords.length && styleMap.size) {
      const need = missingTracks(loadWrittenTracks);
      if (need.length) {
        const styleId = resolveStyleId(styleCatalog, kompStyle.value || 'pop-rock');
        const bars = barStarts(loadMidi, loadDuration);
        const auto = generateAutokomp(
          { barStarts: bars, chords: loadChords, sections: loadSections, duration: loadDuration },
          {
            styleId,
            variant: kompVariantPref,
            humanize: true,
            generate: need,
            dynamics: 'mf',
            styles: styleMap,
            resolveStyleId: (id) => resolveStyleId(styleCatalog, id),
          },
        );
        loadEvents = [...loadWrittenEvents, ...auto].sort((a, b) => a.time - b.time);
      }
    }

    const coldLoad = !engine.isCoreReady() || engine.willLoadNewInstruments(loadEvents);
    if (coldLoad) showLoadingModal('Laddar ljudmotor…');
    setStatus('Laddar ljud…');
    if (!songLoadGuard.isActive(loadToken)) return;

    engine.beginSongPrepare(loadToken);
    try {
      const ready = await engine.prepareInstrumentsForEvents(loadEvents, loadToken);
      if (!ready && songLoadGuard.isActive(loadToken)) {
        throw new Error('Ljudladdning avbröts');
      }
    } catch (err) {
      if (!songLoadGuard.isActive(loadToken)) return;
      hideLoadingModal(`Kunde inte ladda ljud: ${err.message || err}`);
      throw err;
    }
    hideLoadingModal();
    if (typeof console !== 'undefined' && console.info) {
      const m = engine.getLoadMetrics();
      console.info('[notlanken] time-to-ready', {
        ms: Math.round(m.lastPrepareMs),
        cold: coldLoad,
        buffers: m.bufferCount,
      });
    }
    if (!coldLoad && statusEl.textContent === 'Laddar ljud…') setStatus('');
    if (!songLoadGuard.isActive(loadToken)) return;

    midi = loadMidi;
    writtenEvents = loadWrittenEvents;
    writtenTracks = loadWrittenTracks;
    sections = loadSections;
    chords = loadChords;
    duration = loadDuration;
    kompDirectives = loadKompDirectives;
    const stil = resolveStyleId(styleCatalog, kompDirectives.style);
    if (stil && styleMap.has(stil)) {
      kompStyle.value = stil;
    } else if (styleCatalog && midi) {
      const sig = midi.header.timeSignatures?.[0]?.timeSignature || [4, 4];
      kompStyle.value = defaultStyleForMeter(styleCatalog, sig[0], sig[1]);
    }
    sessionNotes = loadNotes(song.file);
    position = 0;
    kompOn = true;
    rebuildEvents({ reschedule: false });
    buildMixerUi();
    updateAutokompUi();

    if (!songLoadGuard.isActive(loadToken)) return;
    timeTotal.textContent = formatClock(duration);
    renderTimeline();
    renderNotesList();
    updateTransportUi();
    updatePositionUi();
    setStatus('');
    renderSongList(songFilter?.value || '');
  } catch (e) {
    if (!songLoadGuard.isActive(loadToken)) return;
    hideLoadingModal(`Kunde inte ladda: ${e.message}`);
    setStatus(`Kunde inte ladda: ${e.message}`, true);
  } finally {
    if (songLoadGuard.isActive(loadToken)) {
      audioBusy = false;
      updateTransportUi();
    }
  }
}

function renderTimeline() {
  timelineSections.innerHTML = '';
  timelineNotes.innerHTML = '';
  if (!duration) {
    renderLane();
    return;
  }

  for (const m of sections) {
    const pct = (m.time / duration) * 100;
    const el = document.createElement('button');
    el.type = 'button';
    el.className = 'timeline-marker section';
    el.style.left = `${pct}%`;
    el.title = m.label;
    el.textContent = m.label.length > 10 ? m.label.slice(0, 9) + '…' : m.label;
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      seekTo(m.time, true);
    });
    timelineSections.appendChild(el);
  }

  for (const n of sessionNotes) {
    const pct = (n.time / duration) * 100;
    const el = document.createElement('button');
    el.type = 'button';
    el.className = `timeline-marker note note-${n.type}`;
    el.style.left = `${pct}%`;
    el.title = n.text;
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      seekTo(n.time, true);
    });
    timelineNotes.appendChild(el);
  }

  renderLane();
}

const LANE_PAD = 4;
const LANE_MIN_BAR_PX = 76;
let lanePps = 40;
let laneSectionEls = [];
let lanePinnedLabel = '';
let lanePinnedWidth = 0;

function laneItem(tag, className, time, text) {
  const el = document.createElement(tag);
  if (tag === 'button') el.type = 'button';
  el.className = className;
  el.style.left = `${time * lanePps}px`;
  if (text != null) el.textContent = text;
  return el;
}

const ROLL_COLORS = {
  piano: '#88c0d0',
  bass: '#a3be8c',
  brass: '#ebcb8b',
  other: '#b48ead',
  drums: '#d08770',
};

/** @param {string} hex */
function rollRgb(hex) {
  const h = hex.replace('#', '');
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

/**
 * Skeuomorphic glass bar — gradient fill + light top / dark bottom edge (canvas-only, no filters).
 * @param {CanvasRenderingContext2D} ctx
 */
function fillGlassNote(ctx, x, y, w, h, hex, active) {
  const { r, g, b } = rollRgb(hex);
  const aTop = active ? 0.95 : 0.78;
  const aMid = active ? 0.88 : 0.68;
  const aBot = active ? 0.82 : 0.58;
  const grad = ctx.createLinearGradient(x, y, x, y + h);
  grad.addColorStop(0, `rgba(${Math.min(255, r + 48)},${Math.min(255, g + 48)},${Math.min(255, b + 48)},${aTop})`);
  grad.addColorStop(0.42, `rgba(${r},${g},${b},${aMid})`);
  grad.addColorStop(1, `rgba(${Math.max(0, r - 42)},${Math.max(0, g - 42)},${Math.max(0, b - 42)},${aBot})`);
  ctx.fillStyle = grad;
  ctx.fillRect(x, y, w, h);
  const hi = active ? 0.58 : 0.38;
  const lo = active ? 0.38 : 0.28;
  ctx.strokeStyle = `rgba(255,255,255,${hi})`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x + 0.5, y + 0.5);
  ctx.lineTo(x + Math.max(1, w) - 0.5, y + 0.5);
  ctx.stroke();
  ctx.strokeStyle = `rgba(0,0,0,${lo})`;
  ctx.beginPath();
  ctx.moveTo(x + 0.5, y + Math.max(1, h) - 0.5);
  ctx.lineTo(x + Math.max(1, w) - 0.5, y + Math.max(1, h) - 0.5);
  ctx.stroke();
}
let rollCtx = null;
let rollW = 0;
let rollH = 0;
let rollMin = 48;
let rollMax = 72;
let rollMaxDur = 2;

function setupRoll() {
  const dpr = window.devicePixelRatio || 1;
  rollW = lane.clientWidth || 320;
  rollH = lane.clientHeight || 136;
  laneRoll.width = Math.round(rollW * dpr);
  laneRoll.height = Math.round(rollH * dpr);
  rollCtx = laneRoll.getContext('2d');
  rollCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

  let lo = 127;
  let hi = 0;
  let maxDur = 0;
  for (const e of events) {
    maxDur = Math.max(maxDur, e.duration);
    if (e.group === 'drums') continue;
    lo = Math.min(lo, e.midi);
    hi = Math.max(hi, e.midi);
  }
  if (lo > hi) {
    lo = 48;
    hi = 72;
  }
  rollMin = lo - 1;
  rollMax = hi + 1;
  rollMaxDur = Math.min(10, Math.max(0.5, maxDur));
}

function drawRoll() {
  if (!rollCtx) return;
  const ctx = rollCtx;
  ctx.clearRect(0, 0, rollW, rollH);
  if (!events.length) return;

  const top = 62;
  const gloss = ctx.createLinearGradient(0, 0, 0, top);
  gloss.addColorStop(0, 'rgba(255,255,255,0.14)');
  gloss.addColorStop(0.55, 'rgba(255,255,255,0.04)');
  gloss.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gloss;
  ctx.fillRect(0, 0, rollW, top);
  const bottom = rollH - 24;
  const h = Math.max(10, bottom - top);
  const span = rollMax - rollMin;
  const noteH = Math.max(2, Math.min(7, h / (span + 1)));
  const windowEnd = position + rollW / lanePps;

  let lo = 0;
  let hi = events.length;
  const from = position - rollMaxDur;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (events[mid].time < from) lo = mid + 1;
    else hi = mid;
  }

  for (let i = lo; i < events.length; i++) {
    const e = events[i];
    if (e.time > windowEnd) break;
    const x = (e.time - position) * lanePps;
    const w = Math.max(2, e.duration * lanePps);
    if (x + w < 0) continue;
    const active = e.time <= position && position < e.time + e.duration;
    const color = ROLL_COLORS[e.group] || ROLL_COLORS.other;
    if (e.group === 'drums') {
      ctx.globalAlpha = active ? 1 : 0.75;
      fillGlassNote(ctx, x, bottom + 4, Math.min(w, 5), 8, color, active);
      ctx.globalAlpha = 1;
      continue;
    }
    const y = top + ((rollMax - e.midi) / span) * (h - noteH);
    ctx.globalAlpha = 1;
    fillGlassNote(ctx, x, y, w, noteH, color, active);
  }
}

function laneVisibleBars() {
  const w = lane?.clientWidth || 320;
  if (w < 380) return 3;
  if (w < 520) return 4;
  return 5;
}

function chordBarIndex(bars, time) {
  let idx = 0;
  for (let i = 0; i < bars.length; i++) {
    if (bars[i] <= time + 0.001) idx = i;
  }
  return idx;
}

function appendLaneChords(bars, barDur) {
  const barPx = lanePps * barDur;
  /** @type {Map<number, { time: number, symbol: string }[]>} */
  const byBar = new Map();
  for (const c of chords) {
    const bi = chordBarIndex(bars, c.time);
    if (!byBar.has(bi)) byBar.set(bi, []);
    byBar.get(bi).push(c);
  }

  for (const [bi, list] of byBar) {
    list.sort((a, b) => a.time - b.time);
    const barStart = bars[bi] ?? 0;
    const n = list.length;
    const slotW = Math.max(28, barPx / n - 3);

    list.forEach((c, idx) => {
      const el = document.createElement('span');
      el.className = 'lane-chord' + (n > 1 ? ' lane-chord-stacked' : '');
      const x = n === 1
        ? c.time * lanePps
        : barStart * lanePps + idx * (barPx / n) + 2;
      el.style.left = `${x}px`;
      if (n > 1) {
        el.style.top = `${1.65 + idx * 1.05}rem`;
        el.style.maxWidth = `${Math.max(32, slotW)}px`;
      }
      let label = c.symbol;
      if (slotW < 52 && label.length > 7) {
        label = `${label.slice(0, 6)}…`;
      }
      el.textContent = label;
      el.title = c.symbol;
      laneTrack.appendChild(el);
    });
  }
}

function renderLane() {
  laneTrack.innerHTML = '';
  laneSectionEls = [];
  lanePinnedLabel = '';
  if (!midi || !duration) {
    lanePinned.hidden = true;
    rollCtx = null;
    return;
  }
  setupRoll();

  const width = lane.clientWidth || 320;
  const bars = barStarts(midi, duration);
  const barDur = bars.length > 1 ? bars[1] - bars[0] : 2;
  const visibleBars = laneVisibleBars();
  lanePps = Math.max(width / (visibleBars * barDur), LANE_MIN_BAR_PX / barDur);
  laneTrack.style.width = `${duration * lanePps + width}px`;

  bars.forEach((time, i) => {
    const line = laneItem('div', 'lane-bar', time);
    const num = document.createElement('span');
    num.textContent = String(i + 1);
    line.appendChild(num);
    laneTrack.appendChild(line);
  });

  appendLaneChords(bars, barDur);

  for (const s of sections) {
    const el = laneItem('button', 'lane-section', s.time, s.label);
    el.title = s.label;
    el.addEventListener('click', () => seekTo(s.time, isPlaying));
    laneTrack.appendChild(el);
    laneSectionEls.push(el);
  }

  for (const n of sessionNotes) {
    const el = laneItem('button', `lane-note note-${n.type}`, n.time);
    el.title = n.text;
    el.addEventListener('click', () => seekTo(n.time, isPlaying));
    laneTrack.appendChild(el);
  }
}

function updateLane() {
  if (!midi || !duration) return;
  laneTrack.style.transform = `translateX(${-position * lanePps}px)`;
  drawRoll();

  let current = null;
  let next = null;
  for (const s of sections) {
    if (s.time <= position + 0.001) current = s;
    else {
      next = s;
      break;
    }
  }

  laneSectionEls.forEach((el, i) => {
    el.style.visibility = sections[i].time <= position + 0.001 ? 'hidden' : 'visible';
  });

  if (!current) {
    lanePinned.hidden = true;
    return;
  }
  lanePinned.hidden = false;
  if (lanePinnedLabel !== current.label) {
    lanePinned.textContent = current.label;
    lanePinnedLabel = current.label;
    lanePinnedWidth = lanePinned.offsetWidth;
  }

  let shift = 0;
  if (next) {
    const nextX = (next.time - position) * lanePps;
    const right = LANE_PAD + lanePinnedWidth + 6;
    if (nextX < right) shift = nextX - right;
  }
  lanePinned.style.transform = `translateX(${shift}px)`;
}

function bindLane() {
  let dragging = false;
  let moved = false;
  let startX = 0;
  let startPos = 0;

  lane.addEventListener('pointerdown', (e) => {
    if (!duration) return;
    dragging = true;
    moved = false;
    startX = e.clientX;
    startPos = position;
  });
  lane.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    if (!moved) {
      if (Math.abs(dx) < 5) return;
      moved = true;
      scrubbing = true;
      lane.setPointerCapture(e.pointerId);
    }
    position = Math.max(0, Math.min(duration, startPos - dx / lanePps));
    updatePositionUi();
  });
  const end = async (e) => {
    if (!dragging) return;
    dragging = false;
    if (!moved) return;
    scrubbing = false;
    try {
      lane.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
    await seekTo(position, isPlaying);
  };
  lane.addEventListener('pointerup', end);
  lane.addEventListener('pointercancel', end);
  window.addEventListener('resize', () => {
    renderLane();
    updateLane();
  });
}

function renderNotesList() {
  notesList.innerHTML = '';
  const sorted = [...sessionNotes].sort((a, b) => a.time - b.time);
  for (const n of sorted) {
    const li = document.createElement('li');
    li.className = `notes-item note-${n.type}`;
    const meta = midi ? formatBarBeat(midi, n.time) : formatClock(n.time);
    li.innerHTML = `
      <div class="notes-item-head">
        <strong>[${noteTypeLabel(n.type)}]</strong>
        <span>${meta} (${formatClock(n.time)})</span>
        <button type="button" class="ghost small" data-jump="${n.id}">Gå hit</button>
        <button type="button" class="ghost small danger" data-del="${n.id}">Ta bort</button>
      </div>
      <textarea class="notes-edit" data-id="${n.id}" rows="2">${n.text}</textarea>
    `;
    notesList.appendChild(li);
  }

  notesList.querySelectorAll('[data-jump]').forEach((b) => {
    b.addEventListener('click', () => {
      const id = b.getAttribute('data-jump');
      const note = sessionNotes.find((x) => x.id === id);
      if (note) seekTo(note.time, true);
    });
  });
  notesList.querySelectorAll('[data-del]').forEach((b) => {
    b.addEventListener('click', () => {
      const id = b.getAttribute('data-del');
      sessionNotes = sessionNotes.filter((x) => x.id !== id);
      persistNotes();
      renderTimeline();
      renderNotesList();
    });
  });
  notesList.querySelectorAll('.notes-edit').forEach((ta) => {
    ta.addEventListener('change', () => {
      const id = ta.getAttribute('data-id');
      const note = sessionNotes.find((x) => x.id === id);
      if (note) {
        note.text = ta.value;
        persistNotes();
        renderTimeline();
      }
    });
  });
}

function persistNotes() {
  if (currentSong) saveNotes(currentSong.file, sessionNotes);
}

function updatePositionUi() {
  const pct = duration ? (position / duration) * 100 : 0;
  timelinePlayhead.style.left = `${pct}%`;
  if (duration) {
    timeline.setAttribute('aria-valuenow', String(Math.round(pct)));
    timeline.setAttribute('aria-valuetext', `${formatClock(position)} av ${formatClock(duration)}`);
  }
  updateLane();
  const elapsed = formatClock(position);
  timeElapsed.textContent = elapsed;
  if (timeElapsedDock) timeElapsedDock.textContent = elapsed;
  if (timeRemaining) {
    const left = Math.max(0, duration - position);
    timeRemaining.textContent = `-${formatClock(left)}`;
  }
  if (midi) timeBarBeat.textContent = formatBarBeat(midi, position);
  const chord = chordAtTime(chords, position);
  if (chord) {
    chordLine.hidden = false;
    chordLine.textContent = chord;
  } else {
    chordLine.hidden = true;
    chordLine.textContent = '';
  }
  syncTransportKompKey();
}

function updateTransportUi() {
  const ready = !!midi && !audioBusy;
  if (btnPlayPause) {
    btnPlayPause.disabled = !ready;
    btnPlayPause.setAttribute('aria-pressed', String(isPlaying));
    btnPlayPause.setAttribute('aria-label', isPlaying ? 'Paus' : 'Spela');
    btnPlayPause.title = isPlaying ? 'Paus (mellanslag)' : 'Spela (mellanslag)';
    btnPlayPause.classList.toggle('is-active', isPlaying);
  }
  btnStop.disabled = !midi || audioBusy;
  if (btnPrev) btnPrev.disabled = !midi || audioBusy;
  if (btnNext) btnNext.disabled = !midi || audioBusy;
  const block = document.querySelector('.transport-block');
  if (block) block.classList.toggle('is-playing', isPlaying);
  const transportV2 = document.querySelector('.transport-v2');
  const kompVisible = autokompApplies();
  if (transportV2) transportV2.classList.toggle('has-komp-chip', kompVisible);
  if (btnKompQuick) btnKompQuick.hidden = !kompVisible;
  if (lcdTitle && currentSong) {
    lcdTitle.dataset.state = isPlaying ? 'spelar' : audioBusy ? 'laddar' : 'paus';
  }
}

function currentPositionFromClock() {
  if (!isPlaying || !engine.ac) return position;
  return playStartPos + (engine.ac.currentTime - playStartAc) * engine.rate;
}

function tick() {
  if (!isPlaying || scrubbing) return;
  position = Math.min(duration, currentPositionFromClock());
  updatePositionUi();
  if (position >= duration - 0.02) {
    pause();
    position = duration;
    updatePositionUi();
    return;
  }
  raf = requestAnimationFrame(tick);
}

async function startPlayback(fromSeconds) {
  if (!midi || audioBusy) return;
  const playToken = ++playbackSeq;
  audioBusy = true;
  updateTransportUi();
  setStatus('Förbereder uppspelning…');
  await engine.ensureContext();
  if (playToken !== playbackSeq) {
    audioBusy = false;
    updateTransportUi();
    return;
  }
  try {
    if (!engine.prepared) {
      const ready = await engine.prepareInstrumentsForEvents(
        events.length ? events : writtenEvents,
      );
      if (playToken !== playbackSeq) {
        audioBusy = false;
        updateTransportUi();
        return;
      }
      if (!ready) {
        audioBusy = false;
        updateTransportUi();
        setStatus('Ljudmotorn håller på att ladda…', true);
        return;
      }
    }
  } catch (err) {
    if (playToken !== playbackSeq) {
      audioBusy = false;
      updateTransportUi();
      return;
    }
    audioBusy = false;
    updateTransportUi();
    setStatus(`Kunde inte ladda ljud: ${err.message || err}`, true);
    return;
  }
  if (playToken !== playbackSeq) {
    audioBusy = false;
    updateTransportUi();
    return;
  }
  setStatus('');
  engine.stopAll();
  position = Math.max(0, Math.min(duration, fromSeconds));
  playStartPos = position;
  playStartAc = engine.ac.currentTime;
  try {
    const scheduled = engine.schedule(events, position, duration + 1);
    if (!scheduled) {
      audioBusy = false;
      updateTransportUi();
      setStatus('Kunde inte starta uppspelning — ljudmotorn är inte redo.', true);
      return;
    }
  } catch (err) {
    audioBusy = false;
    updateTransportUi();
    setStatus(`Kunde inte starta uppspelning: ${err.message || err}`, true);
    return;
  }
  if (playToken !== playbackSeq) {
    engine.stopAll();
    audioBusy = false;
    updateTransportUi();
    return;
  }
  isPlaying = true;
  audioBusy = false;
  updateTransportUi();
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(tick);
}

function pause() {
  cancelInFlightPlayback();
  if (isPlaying && engine.ac) {
    position = currentPositionFromClock();
  }
  isPlaying = false;
  engine.stopAll();
  cancelAnimationFrame(raf);
  updateTransportUi();
  updatePositionUi();
}

function stop() {
  pause();
  position = 0;
  updatePositionUi();
}

async function seekTo(sec, resumeIfPlaying = false) {
  const wasPlaying = isPlaying;
  pause();
  position = Math.max(0, Math.min(duration, sec));
  updatePositionUi();
  if (wasPlaying || resumeIfPlaying) await startPlayback(position);
}

function autokompApplies() {
  return !!(midi && chords.length && missingTracks(writtenTracks).length);
}

function syncKompStyleTriggerLabel() {
  if (!kompStyleTrigger || !kompStyle) return;
  const opt = kompStyle.selectedOptions?.[0];
  kompStyleTrigger.textContent = opt?.textContent || kompStyle.value || 'Stil';
}

function closeKompStyleMenu() {
  if (!kompStyleList || !kompStyleTrigger) return;
  kompStyleList.hidden = true;
  kompStyleTrigger.setAttribute('aria-expanded', 'false');
}

function updateAutokompUi() {
  if (!kompBar) return;
  const applies = autokompApplies();
  kompBar.hidden = !applies;
  if (!applies) {
    closeKompStyleMenu();
    return;
  }
  if (kompSwitch) kompSwitch.setAttribute('aria-checked', String(kompOn));
  if (kompStylePicker) kompStylePicker.hidden = !kompOn;
  syncKompStyleTriggerLabel();
  if (btnKompQuick) btnKompQuick.hidden = !applies;
}

/** Coalesce komp UI refreshes so rapid style swaps stay responsive. */
let kompRefreshRaf = 0;
function requestKompRefresh() {
  if (kompRefreshRaf) cancelAnimationFrame(kompRefreshRaf);
  kompRefreshRaf = requestAnimationFrame(() => {
    kompRefreshRaf = 0;
    const prevGroups = groupsInSong().join(',');
    rebuildEvents();
    if (groupsInSong().join(',') !== prevGroups) buildMixerUi();
    renderLane();
  });
}

function rebuildEvents({ reschedule = true } = {}) {
  const need = missingTracks(writtenTracks);
  const playing = !!(reschedule && isPlaying && engine.ac);
  const p = playing ? currentPositionFromClock() : position;
  // Style/variant swaps take effect from the next bar — only regenerate from there
  // so mid-play changes stay cheap and do not re-arm the whole chart.
  const from = playing ? nextBarStart(p) : 0;

  let freshAuto = [];
  if (kompOn && chords.length && need.length && styleMap.size && midi) {
    const styleId = resolveStyleId(styleCatalog, kompStyle.value || 'pop-rock');
    const bars = barStarts(midi, duration);
    freshAuto = generateAutokomp(
      { barStarts: bars, chords, sections, duration },
      {
        styleId,
        variant: kompVariantPref,
        humanize: true,
        generate: need,
        dynamics: 'mf',
        styles: styleMap,
        resolveStyleId: (id) => resolveStyleId(styleCatalog, id),
        fromTime: playing ? from : undefined,
      },
    );
  }

  if (playing && from > 0) {
    autoEvents = [
      ...autoEvents.filter((e) => e.time < from - 0.001),
      ...freshAuto,
    ];
  } else {
    autoEvents = freshAuto;
  }

  autoGroups = new Set();
  for (const e of autoEvents) autoGroups.add(e.group);

  events = [...writtenEvents, ...autoEvents].sort((a, b) => a.time - b.time);
  if (duration && events.length) {
    duration = Math.max(duration, events[events.length - 1].time + 0.5);
  }
  updateAutokompUi();
  if (playing) {
    // Cut hanging notes; written keeps going from now, autokomp from next bar.
    // Lookahead scheduler only arms a few seconds — must not hang the UI.
    engine.stopAll();
    position = p;
    playStartPos = p;
    playStartAc = engine.ac.currentTime;
    const mixed = [
      ...writtenEvents.filter((e) => e.time >= p - 0.001),
      ...autoEvents.filter((e) => e.time >= from - 0.001),
    ].sort((a, b) => a.time - b.time);
    if (!engine.schedule(mixed, p, duration + 1)) {
      isPlaying = false;
      updateTransportUi();
      setStatus('Kunde inte fortsätta uppspelning — ljudmotorn är inte redo.', true);
      return;
    }
    // Keep the transport RAF alive across stopAll/reschedule.
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(tick);
  }
}

function nextBarStart(seconds) {
  const bars = barStarts(midi, duration + 4);
  for (const t of bars) {
    if (t > seconds + 0.02) return t;
  }
  return seconds;
}

function groupsInSong() {
  const used = new Set(events.map((e) => e.group));
  return GROUPS.filter((g) => used.has(g));
}

function buildMixerUi() {
  const present = groupsInSong();
  for (const g of GROUPS) {
    if (!present.includes(g)) engine.setGroupMixer(g, { solo: false, mute: false });
  }

  mixerGroups.innerHTML = '';
  for (const g of present) {
    const auto = autoGroups.has(g);
    const label = auto ? `${GROUP_LABELS[g]} (auto)` : GROUP_LABELS[g];
    const m = engine.mixer[g];
    const vol = Math.round(m.volume * 100);
    const strip = document.createElement('div');
    strip.className = 'mixer-track-row' + (auto ? ' strip-auto' : '');
    strip.innerHTML = `
      <span class="mixer-track-icon">${GROUP_ICONS[g] || GROUP_ICONS.other}</span>
      <div class="mixer-track-main">
        <span class="mixer-track-label">${label}</span>
        <div class="fader fader-h">
          <input type="range" min="0" max="100" value="${vol}" data-vol="${g}" aria-label="${label} volym">
          <span class="fader-bubble" hidden>${vol}%</span>
        </div>
      </div>
      <div class="mixer-track-actions">
        <button type="button" class="mixer-more-btn" data-more="${g}" aria-expanded="false" aria-label="Spårmeny ${label}" title="Mute och solo"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="6" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="18" r="1.6"/></svg></button>
        <div class="mixer-more-menu" hidden>
          <button type="button" class="mute-big" data-mute="${g}" aria-pressed="${m.mute}" aria-label="Tysta ${label}">${m.mute ? 'Tyst' : 'Ljud'}</button>
          <button type="button" class="chip icon" data-solo="${g}" aria-pressed="${m.solo}" aria-label="Solo ${label}" title="Solo">S</button>
        </div>
      </div>
      <span class="strip-val mixer-track-val" data-vol-val="${g}">${vol}%</span>
    `;
    mixerGroups.appendChild(strip);
  }

  mixerGroups.querySelectorAll('[data-vol]').forEach((el) => {
    const bubble = el.parentElement?.querySelector('.fader-bubble');
    bindHorizontalFader(el, bubble, () => {
      const g = el.getAttribute('data-vol');
      const valEl = mixerGroups.querySelector(`[data-vol-val="${g}"]`);
      if (valEl) valEl.textContent = `${el.value}%`;
      engine.setGroupMixer(g, { volume: el.value / 100 });
      saveMixerSettings(engine, { masterVol, reverb: reverbSlider });
    });
  });
  mixerGroups.querySelectorAll('[data-mute]').forEach((el) => {
    el.addEventListener('click', () => {
      const on = el.getAttribute('aria-pressed') !== 'true';
      el.setAttribute('aria-pressed', String(on));
      el.textContent = on ? 'Tyst' : 'Ljud';
      engine.setGroupMixer(el.getAttribute('data-mute'), { mute: on });
      saveMixerSettings(engine, { masterVol, reverb: reverbSlider });
    });
  });
  mixerGroups.querySelectorAll('[data-solo]').forEach((el) => {
    el.addEventListener('click', () => {
      const on = el.getAttribute('aria-pressed') !== 'true';
      el.setAttribute('aria-pressed', String(on));
      engine.setGroupMixer(el.getAttribute('data-solo'), { solo: on });
      saveMixerSettings(engine, { masterVol, reverb: reverbSlider });
    });
  });
  mixerGroups.querySelectorAll('.mixer-more-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const menu = btn.parentElement?.querySelector('.mixer-more-menu');
      if (!menu) return;
      const willOpen = menu.hidden;
      mixerGroups.querySelectorAll('.mixer-more-menu').forEach((m) => { m.hidden = true; });
      mixerGroups.querySelectorAll('.mixer-more-btn').forEach((b) => {
        b.setAttribute('aria-expanded', 'false');
      });
      if (willOpen) {
        menu.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
}

function openNoteDialog(type = 'note') {
  if (!midi || !currentSong) return;
  pendingNoteType = type;
  noteDialogOpen = true;
  noteDialogMeta.textContent = `${formatBarBeat(midi, position)} · ${formatClock(position)}`;
  noteText.value = '';
  noteDialogTitle.textContent = `Ny anteckning · ${noteTypeLabel(type)}`;
  noteDialog.showModal();
  noteText.focus();
}

function saveNoteFromDialog() {
  const text = noteText.value.trim();
  if (!text || !currentSong) return;
  sessionNotes.push({
    id: crypto.randomUUID(),
    type: pendingNoteType,
    time: position,
    text,
    created: Date.now(),
  });
  persistNotes();
  renderTimeline();
  renderNotesList();
  noteDialogOpen = false;
  noteDialog.close();
}

function copyNotesToClipboard() {
  if (!currentSong || !midi) return;
  const lines = [
    `Låt: ${currentSong.title} – fil: ${currentSong.file}`,
    '',
  ];
  for (const n of [...sessionNotes].sort((a, b) => a.time - b.time)) {
    lines.push(
      `[${noteTypeLabel(n.type)}] ${formatBarBeat(midi, n.time)} (${formatClock(n.time)}): ${n.text}`,
    );
  }
  navigator.clipboard.writeText(lines.join('\n')).then(
    () => setStatus('Kopierat till urklipp.'),
    () => setStatus('Kunde inte kopiera.', true),
  );
}

function timelineClientToTime(clientX) {
  const rect = timelineRail.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  return ratio * duration;
}

function bindTimeline() {
  const onPointerDown = (e) => {
    if (!duration) return;
    scrubbing = true;
    timeline.setPointerCapture(e.pointerId);
    const t = timelineClientToTime(e.clientX);
    position = t;
    updatePositionUi();
  };
  const onPointerMove = (e) => {
    if (!scrubbing) return;
    position = timelineClientToTime(e.clientX);
    updatePositionUi();
  };
  const onPointerUp = async (e) => {
    if (!scrubbing) return;
    scrubbing = false;
    try {
      timeline.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
    await seekTo(position, isPlaying);
  };
  timeline.addEventListener('pointerdown', onPointerDown);
  timeline.addEventListener('pointermove', onPointerMove);
  timeline.addEventListener('pointerup', onPointerUp);
  timeline.addEventListener('click', (e) => {
    if (e.target.closest('.timeline-marker')) return;
    seekTo(timelineClientToTime(e.clientX), isPlaying);
  });
  timeline.addEventListener('keydown', (e) => {
    if (!duration || !midi) return;
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      seekTo(jumpBars(midi, position, -1), isPlaying);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      seekTo(jumpBars(midi, position, 1), isPlaying);
    } else if (e.key === 'Home') {
      e.preventDefault();
      seekTo(0, isPlaying);
    } else if (e.key === 'End') {
      e.preventDefault();
      seekTo(duration, isPlaying);
    }
  });
}

btnPlayPause?.addEventListener('click', async () => {
  await engine.ensureContext();
  if (isPlaying) pause();
  else await startPlayback(position);
});
btnStop.addEventListener('click', () => stop());
btnPrev?.addEventListener('click', () => {
  if (!midi) return;
  seekTo(jumpBars(midi, position, -1), isPlaying);
});
btnNext?.addEventListener('click', () => {
  if (!midi) return;
  seekTo(jumpBars(midi, position, 1), isPlaying);
});
btnKompQuick?.addEventListener('click', () => {
  if (!kompBar || kompBar.hidden) return;
  kompBar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  kompSwitch?.focus();
});

bindModuleDialog(speedDialog, btnSpeed, speedClose);
bindModuleDialog(mixerDialog, btnMixer, mixerClose);

document.addEventListener('click', () => {
  mixerGroups?.querySelectorAll('.mixer-more-menu').forEach((m) => { m.hidden = true; });
  mixerGroups?.querySelectorAll('.mixer-more-btn').forEach((b) => {
    b.setAttribute('aria-expanded', 'false');
  });
});

const SPEED_GROUPS = [
  { label: 'Långsam', speeds: [0.5, 0.75] },
  { label: 'Normal', speeds: [1, 1.1, 1.25] },
  { label: 'Snabb', speeds: [1.5, 2, 3] },
];

function formatSpeed(s) {
  return `${String(s).replace('.', ',')}x`;
}

function setSpeed(speed) {
  const resumeAt = isPlaying ? currentPositionFromClock() : null;
  engine.rate = speed;
  speedOptions.querySelectorAll('button').forEach((b) => {
    b.setAttribute('aria-pressed', String(Number(b.dataset.speed) === speed));
  });
  if (resumeAt != null) startPlayback(resumeAt);
}

for (const group of SPEED_GROUPS) {
  const wrap = document.createElement('div');
  wrap.className = 'speed-group';
  const lab = document.createElement('span');
  lab.className = 'speed-group-label';
  lab.textContent = group.label;
  const chips = document.createElement('div');
  chips.className = 'speed-group-chips';
  for (const s of group.speeds) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip nl-knob-chip';
    b.dataset.speed = String(s);
    b.textContent = formatSpeed(s);
    b.setAttribute('aria-pressed', String(s === 1));
    b.addEventListener('click', () => setSpeed(s));
    chips.appendChild(b);
  }
  wrap.appendChild(lab);
  wrap.appendChild(chips);
  speedOptions.appendChild(wrap);
}

bindHorizontalFader(reverbSlider, $('reverb-bubble'), () => {
  reverbVal.textContent = `${reverbSlider.value}%`;
  engine.setReverbAmount(Number(reverbSlider.value) / 100);
  saveMixerSettings(engine, { masterVol, reverb: reverbSlider });
});

bindHorizontalFader(masterVol, $('master-vol-bubble'), () => {
  masterVolVal.textContent = `${masterVol.value}%`;
  engine.setMasterVolume(Number(masterVol.value) / 100);
  saveMixerSettings(engine, { masterVol, reverb: reverbSlider });
});

btnCopyLink?.addEventListener('click', copySongLink);

noteAdd.querySelectorAll('button').forEach((b) => {
  b.addEventListener('click', () => openNoteDialog(b.getAttribute('data-type')));
});

function goHome() {
  if (location.hash) location.hash = '';
  else showListView();
}

btnBack.addEventListener('click', goHome);
siteHome?.addEventListener('click', (e) => {
  e.preventDefault();
  goHome();
});
window.addEventListener('hashchange', routeFromHash);

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return;
  if (isPlaying) void engine.ensureContext();
});

noteForm.addEventListener('submit', (e) => {
  e.preventDefault();
  saveNoteFromDialog();
});
noteCancel.addEventListener('click', () => {
  noteDialogOpen = false;
  noteDialog.close();
});
noteDialog.addEventListener('close', () => {
  noteDialogOpen = false;
});

btnCopyNotes.addEventListener('click', copyNotesToClipboard);
btnClearNotes.addEventListener('click', () => {
  if (!sessionNotes.length) return;
  if (confirm('Rensa alla anteckningar för denna låt?')) {
    sessionNotes = [];
    persistNotes();
    renderTimeline();
    renderNotesList();
  }
});

document.addEventListener('keydown', (e) => {
  if (!isPlayerView()) return;
  if (noteDialogOpen || isModuleDialogOpen()) return;
  if (isTypingTarget()) return;

  if (e.code === 'Space') {
    e.preventDefault();
    btnPlayPause?.click();
    return;
  }
  if (e.key === 'ArrowLeft' && midi) {
    e.preventDefault();
    seekTo(jumpBars(midi, position, -1), isPlaying);
    return;
  }
  if (e.key === 'ArrowRight' && midi) {
    e.preventDefault();
    seekTo(jumpBars(midi, position, 1), isPlaying);
    return;
  }
  if (e.key === 'b' || e.key === 'B') {
    e.preventDefault();
    openNoteDialog('bug');
    return;
  }
  if (e.key === 'n' || e.key === 'N') {
    e.preventDefault();
    openNoteDialog('note');
    return;
  }
  if (e.key === 'ö' || e.key === 'Ö' || e.key === 'w' || e.key === 'W') {
    e.preventDefault();
    openNoteDialog('onske');
  }
});


function showLoadingModal(msg) {
  let el = document.getElementById('loading-modal');
  if (!el) {
    el = document.createElement('dialog');
    el.id = 'loading-modal';
    el.className = 'loading-modal';
    el.innerHTML = `
      <div class="loading-card">
        <div class="loading-spinner" aria-hidden="true"></div>
        <p class="loading-msg" id="loading-msg"></p>
      </div>
    `;
    document.body.appendChild(el);
  }
  el.querySelector('#loading-msg').textContent = msg;
  el.classList.remove('error');
  if (!el.open) el.showModal();
}

function hideLoadingModal(errMsg) {
  const el = document.getElementById('loading-modal');
  if (!el) return;
  if (errMsg) {
    el.classList.add('error');
    el.querySelector('#loading-msg').textContent = errMsg;
    setTimeout(() => { if (el.open) el.close(); }, 2200);
    return;
  }
  if (el.open) el.close();
}

bindTimeline();
bindLane();

applyMixerSettings(engine, {
  masterVol,
  reverb: reverbSlider,
  masterVolVal,
  reverbVal,
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker
    .register(new URL('sw.js', import.meta.url), { scope: './', type: 'module' })
    .then((reg) => reg.update())
    .catch(() => {});
}

async function initKompUi() {
  if (!kompStyle || !kompSwitch) return;
  const base = new URL('./', import.meta.url).href;
  const loaded = await loadStyles(base);
  styleCatalog = loaded.catalog;
  styleMap = loaded.styles;
  kompStyle.innerHTML = '';
  if (kompStyleList) kompStyleList.innerHTML = '';
  for (const id of styleCatalog.styles) {
    if (!styleMap.has(id)) continue;
    const name = styleMap.get(id).name || id;
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = name;
    kompStyle.appendChild(opt);
    const li = document.createElement('li');
    li.role = 'option';
    li.tabIndex = -1;
    li.dataset.value = id;
    li.textContent = name;
    li.addEventListener('click', () => {
      kompStyle.value = id;
      syncKompStyleTriggerLabel();
      closeKompStyleMenu();
      requestKompRefresh();
    });
    kompStyleList?.appendChild(li);
  }
  kompStyle.value = 'pop-rock';
  syncKompStyleTriggerLabel();
  kompSwitch.addEventListener('click', () => {
    kompOn = kompSwitch.getAttribute('aria-checked') !== 'true';
    updateAutokompUi();
    requestKompRefresh();
  });
  kompStyle.addEventListener('change', () => {
    syncKompStyleTriggerLabel();
    requestKompRefresh();
  });
  kompStyleTrigger?.addEventListener('click', (e) => {
    e.stopPropagation();
    if (kompStylePicker?.hidden || !kompStyleList) return;
    const wasHidden = kompStyleList.hidden;
    kompStyleList.hidden = !wasHidden;
    kompStyleTrigger.setAttribute('aria-expanded', String(!kompStyleList.hidden));
    if (!kompStyleList.hidden) {
      kompStyleList.querySelector(`[data-value="${CSS.escape(kompStyle.value)}"]`)?.focus?.();
    }
  });
  kompStyleList?.addEventListener('click', (e) => e.stopPropagation());
  document.addEventListener('click', () => closeKompStyleMenu());
}

const kompReady = initKompUi().catch((e) => {
  console.error(e);
  setStatus('Kunde inte ladda autokomp-stilar', true);
});

kompReady.then(() => {
  void engine.warmupCore();
  return loadManifest();
}).catch((e) => {
  const li = document.createElement('li');
  li.className = 'status error';
  li.textContent = `Kunde inte ladda låtlistan: ${e.message}`;
  songList.appendChild(li);
});
