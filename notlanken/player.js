import { Midi } from 'https://esm.sh/@tonejs/midi@2.0.28';
import { AudioEngine, GROUPS } from './audio-engine.js';
import {
  barStarts,
  formatBarBeat,
  formatClock,
  jumpBars,
  secondsToBarBeat,
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
} from './autokomp.js';

const engine = new AudioEngine(new URL('./', import.meta.url).href);

const $ = (id) => document.getElementById(id);

const songList = $('song-list');
const viewList = $('view-list');
const playerEl = $('player');
const btnBack = $('btn-back');
const nowPlaying = $('now-playing');
const chordLine = $('chord-line');
const btnPlay = $('btn-play');
const btnPause = $('btn-pause');
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
const kompEnabled = $('komp-enabled');
const kompStyle = $('komp-style');
const kompStatus = $('komp-status');
const kompVariant = document.querySelector('.komp-variant');

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

const GROUP_LABELS = {
  piano: 'Piano',
  bass: 'Bas',
  drums: 'Trummor',
  brass: 'Blås',
  other: 'Övrigt',
};

function setStatus(msg, isError = false) {
  statusEl.textContent = msg || '';
  statusEl.classList.toggle('error', isError);
}

function isTypingTarget() {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable;
}

/** @type {{ file: string, title: string }[]} */
let songs = [];

function isPlayerView() {
  return !playerEl.hidden;
}

function showListView() {
  stop();
  currentSong = null;
  playerEl.hidden = true;
  viewList.hidden = false;
  document.title = 'Notlåda';
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

async function loadManifest() {
  const res = await fetch('midi/songs.json');
  songs = await res.json();
  songList.innerHTML = '';
  for (const song of songs) {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = song.title;
    btn.addEventListener('click', () => {
      engine.ensureContext();
      location.hash = encodeURIComponent(song.file);
    });
    li.appendChild(btn);
    songList.appendChild(li);
  }
  routeFromHash();
}


async function openSong(song) {
  await kompReady;
  engine.stopAll();
  isPlaying = false;
  cancelAnimationFrame(raf);

  midi = null;
  currentSong = song;
  document.title = `${song.title} – Notlåda`;
  nowPlaying.textContent = song.title;
  showPlayerView();
  updateTransportUi();
  setStatus('Laddar MIDI…');

  try {
    const res = await fetch(`midi/${encodeURIComponent(song.file)}`);
    const buf = await res.arrayBuffer();
    midi = new Midi(buf);
    writtenEvents = engine.buildEvents(midi);
    writtenTracks = detectWrittenTracks(midi);
    duration = Math.max(
      midi.duration,
      writtenEvents.length ? writtenEvents[writtenEvents.length - 1].time + 0.5 : 0,
    );
    setStatus('Laddar ljud…');
    engine.prepared = false;
    await engine.preparePlayback();
    if (currentSong !== song) return;
    const meta = parseSongMeta(midi);
    sections = meta.sections;
    chords = meta.chords;
    kompDirectives = parseKompDirectives(midi);
    if (kompDirectives.style && styleMap.has(kompDirectives.style)) {
      kompStyle.value = kompDirectives.style;
    } else if (styleCatalog && midi) {
      const sig = midi.header.timeSignatures?.[0]?.timeSignature || [4, 4];
      kompStyle.value = defaultStyleForMeter(styleCatalog, sig[0], sig[1]);
    }
    sessionNotes = loadNotes(song.file);
    position = 0;
    rebuildEvents({ reschedule: false });
    buildMixerUi();

    if (currentSong !== song) return;
    timeTotal.textContent = formatClock(duration);
    renderTimeline();
    renderNotesList();
    updateTransportUi();
    updatePositionUi();
    setStatus('');
  } catch (e) {
    setStatus(`Kunde inte ladda: ${e.message}`, true);
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

const LANE_BARS = 8;
const LANE_PAD = 4;
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

  const top = 54;
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
    ctx.globalAlpha = active ? 1 : 0.7;
    ctx.fillStyle = ROLL_COLORS[e.group] || ROLL_COLORS.other;
    if (e.group === 'drums') {
      ctx.fillRect(x, bottom + 4, Math.min(w, 4), 8);
      continue;
    }
    const y = top + ((rollMax - e.midi) / span) * (h - noteH);
    ctx.fillRect(x, y, w, noteH);
    if (active) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.strokeRect(x + 0.5, y + 0.5, Math.max(1, w - 1), Math.max(1, noteH - 1));
    }
  }
  ctx.globalAlpha = 1;
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
  lanePps = width / (LANE_BARS * barDur);
  laneTrack.style.width = `${duration * lanePps + width}px`;

  bars.forEach((time, i) => {
    const line = laneItem('div', 'lane-bar', time);
    const num = document.createElement('span');
    num.textContent = String(i + 1);
    line.appendChild(num);
    laneTrack.appendChild(line);
  });

  for (const c of chords) {
    laneTrack.appendChild(laneItem('span', 'lane-chord', c.time, c.symbol));
  }

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
  updateLane();
  timeElapsed.textContent = formatClock(position);
  if (midi) timeBarBeat.textContent = formatBarBeat(midi, position);
  const chord = chordAtTime(chords, position);
  if (chord) {
    chordLine.hidden = false;
    chordLine.textContent = `Ackord: ${chord}`;
  } else {
    chordLine.hidden = true;
  }
}

function updateTransportUi() {
  btnPlay.disabled = !midi;
  btnPause.disabled = !midi || !isPlaying;
  btnStop.disabled = !midi;
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
  if (!midi) return;
  await engine.ensureContext();
  engine.stopAll();
  position = Math.max(0, Math.min(duration, fromSeconds));
  playStartPos = position;
  playStartAc = engine.ac.currentTime;
  isPlaying = true;
  updateTransportUi();
  engine.schedule(events, position, duration + 1);
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(tick);
}

function pause() {
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

function rebuildEvents({ reschedule = true } = {}) {
  autoEvents = [];
  autoGroups = new Set();
  const need = missingTracks(writtenTracks);
  if (kompOn && chords.length && need.length && styleMap.size) {
    const styleId = kompStyle.value || 'pop44';
    const bars = barStarts(midi, duration);
    autoEvents = generateAutokomp(
      { barStarts: bars, chords, sections, duration },
      {
        styleId,
        variant: kompVariantPref,
        humanize: true,
        generate: need,
        dynamics: 'mf',
        styles: styleMap,
      },
    );
    for (const e of autoEvents) autoGroups.add(e.group);
  }
  events = [...writtenEvents, ...autoEvents].sort((a, b) => a.time - b.time);
  if (duration && events.length) {
    duration = Math.max(duration, events[events.length - 1].time + 0.5);
  }
  const parts = needLabel();
  kompStatus.textContent = parts;
  if (reschedule && isPlaying && engine.ac) {
    const p = currentPositionFromClock();
    // Cut hanging notes, then schedule the new mix from the next bar.
    const next = nextBarStart(p);
    engine.stopAll();
    position = p;
    playStartPos = p;
    playStartAc = engine.ac.currentTime;
    const from = next;
    // Keep written notes sounding from now; autokomp changes from next bar.
    const mixed = [
      ...writtenEvents.filter((e) => e.time >= p - 0.001),
      ...autoEvents.filter((e) => e.time >= from - 0.001),
    ].sort((a, b) => a.time - b.time);
    engine.schedule(mixed, p, duration + 1);
  }
}

function needLabel() {
  if (!chords.length) return 'Inga ackordmarkörer – autokomp av';
  const need = missingTracks(writtenTracks);
  if (!need.length) return 'Alla spår skrivna – inget genereras';
  if (!kompOn) return `Komp av (skulle fylla: ${need.join(', ')})`;
  return `Auto: ${need.join(', ')}`;
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
    const send = Math.round(m.reverbSend * 100);
    const strip = document.createElement('div');
    strip.className = 'strip' + (auto ? ' strip-auto' : '');
    strip.innerHTML = `
      <span class="strip-label">${label}</span>
      <button type="button" class="mute-big" data-mute="${g}" aria-pressed="${m.mute}" aria-label="Tysta ${label}">${m.mute ? 'MUTAD' : 'MUTE'}</button>
      <div class="fader">
        <input type="range" min="0" max="100" value="${vol}" data-vol="${g}" aria-label="${label} volym">
      </div>
      <span class="strip-val" data-vol-val="${g}">${vol}</span>
      <div class="strip-buttons">
        <button type="button" class="chip" data-solo="${g}" aria-pressed="${m.solo}" aria-label="Solo ${label}" title="Solo">S</button>
      </div>
      <label class="send">
        <span>Rev</span>
        <input type="range" min="0" max="100" value="${send}" data-send="${g}" aria-label="${label} reverb-send">
      </label>
    `;
    mixerGroups.appendChild(strip);
  }

  mixerGroups.querySelectorAll('[data-vol]').forEach((el) => {
    el.addEventListener('input', () => {
      const g = el.getAttribute('data-vol');
      mixerGroups.querySelector(`[data-vol-val="${g}"]`).textContent = el.value;
      engine.setGroupMixer(g, { volume: el.value / 100 });
    });
  });
  mixerGroups.querySelectorAll('[data-mute]').forEach((el) => {
    el.addEventListener('click', () => {
      const on = el.getAttribute('aria-pressed') !== 'true';
      el.setAttribute('aria-pressed', String(on));
      el.textContent = on ? 'MUTAD' : 'MUTE';
      engine.setGroupMixer(el.getAttribute('data-mute'), { mute: on });
    });
  });
  mixerGroups.querySelectorAll('[data-solo]').forEach((el) => {
    el.addEventListener('click', () => {
      const on = el.getAttribute('aria-pressed') !== 'true';
      el.setAttribute('aria-pressed', String(on));
      engine.setGroupMixer(el.getAttribute('data-solo'), { solo: on });
    });
  });
  mixerGroups.querySelectorAll('[data-send]').forEach((el) => {
    el.addEventListener('input', () => {
      engine.setGroupMixer(el.getAttribute('data-send'), { reverbSend: el.value / 100 });
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
}

btnPlay.addEventListener('click', async () => {
  await engine.ensureContext();
  await startPlayback(position);
});
btnPause.addEventListener('click', () => pause());
btnStop.addEventListener('click', () => stop());

const SPEEDS = [0.5, 0.75, 1, 1.1, 1.25, 1.5, 2, 3];

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

for (const s of SPEEDS) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'chip speed';
  b.dataset.speed = String(s);
  b.textContent = formatSpeed(s);
  b.setAttribute('aria-pressed', String(s === 1));
  b.addEventListener('click', () => setSpeed(s));
  speedOptions.appendChild(b);
}

reverbSlider.addEventListener('input', () => {
  reverbVal.textContent = `${reverbSlider.value}%`;
  engine.setReverbAmount(Number(reverbSlider.value) / 100);
});

masterVol.addEventListener('input', () => {
  masterVolVal.textContent = `${masterVol.value}%`;
  engine.setMasterVolume(Number(masterVol.value) / 100);
});

btnMixer.addEventListener('click', () => {
  const open = mixerPanel.hidden;
  mixerPanel.hidden = !open;
  btnMixer.setAttribute('aria-expanded', String(open));
});

noteAdd.querySelectorAll('button').forEach((b) => {
  b.addEventListener('click', () => openNoteDialog(b.getAttribute('data-type')));
});

btnBack.addEventListener('click', () => {
  if (location.hash) location.hash = '';
  else showListView();
});
window.addEventListener('hashchange', routeFromHash);

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
  if (noteDialogOpen) return;
  if (isTypingTarget()) return;

  if (e.code === 'Space') {
    e.preventDefault();
    if (isPlaying) pause();
    else btnPlay.click();
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

bindTimeline();
bindLane();

async function initKompUi() {
  const base = new URL('./', import.meta.url).href;
  const loaded = await loadStyles(base);
  styleCatalog = loaded.catalog;
  styleMap = loaded.styles;
  kompStyle.innerHTML = '';
  for (const id of styleCatalog.styles) {
    if (!styleMap.has(id)) continue;
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = id;
    kompStyle.appendChild(opt);
  }
  kompStyle.value = 'pop44';
  kompEnabled.addEventListener('change', () => {
    kompOn = kompEnabled.checked;
    rebuildEvents();
    buildMixerUi();
    renderLane();
  });
  kompStyle.addEventListener('change', () => {
    rebuildEvents();
    buildMixerUi();
    renderLane();
  });
  kompVariant.querySelectorAll('button').forEach((b) => {
    b.addEventListener('click', () => {
      kompVariantPref = b.getAttribute('data-variant');
      kompVariant.querySelectorAll('button').forEach((x) => {
        x.setAttribute('aria-pressed', String(x === b));
      });
      rebuildEvents();
      renderLane();
    });
  });
}

const kompReady = initKompUi().catch((e) => {
  console.error(e);
  kompStatus.textContent = 'Kunde inte ladda stilar';
});

kompReady.then(() => loadManifest()).catch((e) => {
  const li = document.createElement('li');
  li.className = 'status error';
  li.textContent = `Kunde inte ladda låtlistan: ${e.message}`;
  songList.appendChild(li);
});
