import { resolveVoice } from './instruments.js';
import { cachedFetch } from './asset-cache.js';
import { SAMPLE_URL_VERSION } from './sample-asset-version.js';
import { SAMPLE_MANIFEST, samplePathsForEvents } from './sample-manifest.js';

const GROUPS = ['piano', 'bass', 'drums', 'brass', 'other'];

/** Fixed send levels per group (× master reverb fader). Not user-editable. */
const INTERNAL_REVERB_SEND = {
  piano: 0.24,
  bass: 0.2,
  drums: 0.1,
  brass: 0.14,
  other: 0.22,
};

const CORE_SAMPLE_FOLDERS = ['samples/piano'];

/** Natural release tail after MIDI note-off (seconds). */
const GROUP_RELEASE = {
  piano: 0.4,
  bass: 0.48,
  drums: 0,
  brass: 0.3,
  other: 0.42,
};

/** Minimum held time so staccato MIDI still has body (seconds). */
const GROUP_MIN_HOLD = {
  piano: 0.05,
  bass: 0.07,
  brass: 0.045,
  other: 0.08,
};

/** Per-group gain before velocity (keeps dense arrangements under headroom) */
const GROUP_HEADROOM = {
  piano: 0.32,
  bass: 0.4,
  drums: 0.45,
  brass: 0.35,
  other: 0.32,
};

/** Kick, snare, hats, cymbals only — toms/toys are not played. */
export const DRUM_MAP = {
  35: '36-kick.ogg',
  36: '36-kick.ogg',
  37: '38-snare.ogg',
  38: '38-snare.ogg',
  39: '38-snare.ogg',
  40: '38-snare.ogg',
  42: '42-closed-hat.ogg',
  44: '42-closed-hat.ogg',
  46: '46-open-hat.ogg',
  49: '49-crash.ogg',
  51: '51-ride.ogg',
  53: '53-ride-bell.ogg',
  57: '49-crash.ogg',
};

/** Relative gain vs other drums (linear; ~0.28 ≈ −11 dB). */
const DRUM_SAMPLE_GAIN = {
  '51-ride.ogg': 0.28,
  '53-ride-bell.ogg': 0.26,
  '49-crash.ogg': 0.55,
};

function drumSampleFile(midi) {
  return DRUM_MAP[midi] || null;
}

function voiceToGroup(voice) {
  if (voice.kind === 'piano') return 'piano';
  if (voice.kind === 'bass') return 'bass';
  if (voice.kind === 'drums') return 'drums';
  if (voice.kind === 'trumpet' || voice.kind === 'trombone' || voice.kind === 'tenor_sax' || voice.kind === 'brass_section') {
    return 'brass';
  }
  return 'other';
}

/** Small room / short hall (~1.1–1.2 s). */
function generateImpulseResponse(ac, duration = 1.15, decay = 5.4, level = 0.26) {
  const rate = ac.sampleRate;
  const len = Math.floor(rate * duration);
  const buf = ac.createBuffer(2, len, rate);
  for (let c = 0; c < 2; c++) {
    const ch = buf.getChannelData(c);
    for (let i = 0; i < len; i++) {
      ch[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay) * level;
    }
  }
  return buf;
}

/** Sample folders required for these events (excluding core piano). */
export function foldersNeededForEvents(events) {
  const folders = new Set();
  for (const ev of events) {
    const { voice } = ev;
    if (!voice) continue;
    if (voice.kind === 'piano') {
      folders.add(voice.sample === 'rhodes' ? 'samples/rhodes' : 'samples/piano');
    } else if (voice.kind === 'bass') {
      folders.add('samples/bass');
    } else if (
      voice.kind === 'trumpet'
      || voice.kind === 'trombone'
      || voice.kind === 'tenor_sax'
      || voice.kind === 'brass_section'
    ) {
      folders.add(`samples/${voice.kind}`);
    }
  }
  for (const f of CORE_SAMPLE_FOLDERS) folders.delete(f);
  return [...folders];
}

let sharedEngine = null;

/** One AudioEngine per page session (decoded buffers stay in memory). */
export function getAudioEngine(baseUrl) {
  if (!sharedEngine) sharedEngine = new AudioEngine(baseUrl);
  return sharedEngine;
}

function scaledGain(velocity, group) {
  const v = Math.max(0, Math.min(1, velocity ?? 0.8));
  const head = GROUP_HEADROOM[group] ?? 0.3;
  return v * head;
}

/**
 * Hold at peak from `when`, then exponential release. Samples already
 * contain attack transients — do not fade in (avoids reverse-swell artefact).
 * @param {AudioParam} gainParam
 */
export function scheduleHeldGainEnvelope(gainParam, when, peak, holdSec, releaseSec) {
  const h = Math.max(0, holdSec);
  const r = Math.max(0.06, releaseSec);
  const p = Math.max(peak, 0.0001);
  gainParam.cancelScheduledValues(when);
  gainParam.setValueAtTime(p, when);
  if (h > 0) gainParam.setValueAtTime(p, when + h);
  gainParam.exponentialRampToValueAtTime(0.0001, when + h + r);
}

/** @returns {{ hold: number, release: number }} sustain + release for held envelopes */
export function noteHoldAndRelease(duration, rate, group) {
  const release = GROUP_RELEASE[group] ?? 0.35;
  const hold = duration > 0
    ? Math.max(duration / rate, GROUP_MIN_HOLD[group] ?? 0.05)
    : 0.35;
  return { hold, release };
}

export class AudioEngine {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : baseUrl + '/';
    /** @type {AudioContext | null} */
    this.ac = null;
    this.master = null;
    this.compressor = null;
    this.reverb = null;
    this.reverbPreDelay = null;
    this.reverbWet = null;
    this.reverbDry = null;
    this.groupNodes = {};
    this.buffers = new Map();
    this.melodicZones = new Map();
    this.sessionId = 0;
    /** @type {Set<AudioBufferSourceNode>} */
    this.activeSources = new Set();
    this.rate = 1;
    this.mixer = {};
    this.prepared = false;
    this._coreReady = false;
    /** @type {Set<string>} */
    this._loadedPaths = new Set();
    /** @type {Set<string>} */
    this._loadedFolders = new Set();
    /** @type {Promise<void> | null} */
    this._warmPromise = null;
    this._lastPrepareMs = 0;
    /** @type {number} Latest song-load token allowed to mark prepared. */
    this._prepareToken = 0;
    /** @type {ReturnType<typeof setInterval> | null} */
    this._schedTimer = null;
    /** @type {null | { events: any[], startSeconds: number, endSeconds: number, index: number, originAc: number, originSong: number, sid: number }} */
    this._schedQueue = null;
    for (const g of GROUPS) {
      this.mixer[g] = { volume: 0.75, mute: false, solo: false };
    }
    this.masterVolume = 0.72;
    this.reverbAmount = 0.08;
    this.pianoSample = 'acoustic';
    /** @type {Record<string, BiquadFilterNode>} */
    this.groupFilters = {};
  }

  async ensureContext() {
    if (!this.ac) {
      this.ac = new AudioContext();
      this.master = this.ac.createGain();
      this.compressor = this.ac.createDynamicsCompressor();
      this.compressor.threshold.setValueAtTime(-22, this.ac.currentTime);
      this.compressor.knee.setValueAtTime(18, this.ac.currentTime);
      this.compressor.ratio.setValueAtTime(6, this.ac.currentTime);
      this.compressor.attack.setValueAtTime(0.003, this.ac.currentTime);
      this.compressor.release.setValueAtTime(0.2, this.ac.currentTime);

      this.reverbDry = this.ac.createGain();
      this.reverbWet = this.ac.createGain();
      this.reverbPreDelay = this.ac.createDelay(0.05);
      this.reverbPreDelay.delayTime.value = 0.016;
      this.reverb = this.ac.createConvolver();
      this.reverb.buffer = generateImpulseResponse(this.ac);
      this.reverbDry.connect(this.master);
      this.reverbPreDelay.connect(this.reverb);
      this.reverb.connect(this.reverbWet);
      this.reverbWet.connect(this.master);
      this.master.connect(this.compressor);
      this.compressor.connect(this.ac.destination);
      this._applyLevels();

      for (const g of GROUPS) {
        const dry = this.ac.createGain();
        const send = this.ac.createGain();
        const filter = this.ac.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.value = g === 'drums' ? 14000 : g === 'bass' ? 6800 : 9800;
        filter.Q.value = 0.7;
        dry.connect(filter);
        filter.connect(this.reverbDry);
        send.connect(this.reverbPreDelay);
        this.groupNodes[g] = { dry, send, filter };
        this.groupFilters[g] = filter;
      }
    }
    if (this.ac.state === 'suspended') await this.ac.resume();
    return this.ac;
  }

  _applyLevels() {
    if (!this.ac || !this.groupNodes.piano) return;
    const solo = GROUPS.some((g) => this.mixer[g].solo);
    this.master.gain.value = this.masterVolume;
    this.reverbWet.gain.value = this.reverbAmount;
    this.reverbDry.gain.value = 1;
    for (const g of GROUPS) {
      const m = this.mixer[g];
      const audible = solo ? m.solo && !m.mute : !m.mute;
      const vol = audible ? m.volume : 0;
      const sendAmt = INTERNAL_REVERB_SEND[g] ?? 0.2;
      this.groupNodes[g].dry.gain.value = vol;
      this.groupNodes[g].send.gain.value = vol * sendAmt;
    }
  }

  listMixerGroups() {
    return GROUPS;
  }

  isCoreReady() {
    return this._coreReady;
  }

  getLoadMetrics() {
    return {
      coreReady: this._coreReady,
      lastPrepareMs: this._lastPrepareMs,
      bufferCount: this.buffers.size,
    };
  }

  willLoadNewInstruments(events) {
    for (const p of samplePathsForEvents(events, Object.values(DRUM_MAP))) {
      if (!this._loadedPaths.has(p)) return true;
    }
    return false;
  }

  warmupCore() {
    if (this._warmPromise) return this._warmPromise;
    this._warmPromise = this._loadPaths(
      samplePathsForEvents([], Object.values(DRUM_MAP)),
      this._prepareToken,
    ).then((ok) => {
      if (ok) {
        this._coreReady = true;
        this._loadedFolders.add('samples/piano');
      }
    }).finally(() => {
      this._warmPromise = null;
    });
    return this._warmPromise;
  }

  setMasterVolume(v) {
    this.masterVolume = v;
    this._applyLevels();
  }

  setReverbAmount(v) {
    this.reverbAmount = v;
    this._applyLevels();
  }

  setGroupMixer(group, patch) {
    if (!this.mixer[group]) return;
    Object.assign(this.mixer[group], patch);
    this._applyLevels();
  }

  stopAll() {
    this._clearScheduleTimer();
    const now = this.ac?.currentTime ?? 0;
    for (const src of this.activeSources) {
      try {
        if (typeof src.stop === 'function') src.stop(now);
      } catch {
        try {
          src.stop();
        } catch {
          /* already stopped */
        }
      }
    }
    this.activeSources.clear();
    this._applyLevels();
    this.sessionId += 1;
  }

  _clearScheduleTimer() {
    if (this._schedTimer != null) {
      clearInterval(this._schedTimer);
      this._schedTimer = null;
    }
    this._schedQueue = null;
  }

  async loadBuffer(path) {
    if (this.buffers.has(path)) return this.buffers.get(path);
    const ac = await this.ensureContext();
    const url = `${this.baseUrl}${path}?v=${encodeURIComponent(SAMPLE_URL_VERSION)}`;
    const res = await cachedFetch(url);
    if (!res.ok) throw new Error(`Sample saknas: ${path}`);
    const arr = await res.arrayBuffer();
    const buf = await ac.decodeAudioData(arr);
    this.buffers.set(path, buf);
    return buf;
  }

  async loadMelodicZones(folder) {
    if (this.melodicZones.has(folder)) return this.melodicZones.get(folder);
    const files = await this._listFolder(folder);
    const zones = [];
    for (const f of files) {
      const name = f.replace('.ogg', '');
      const midi = this._noteNameToMidi(name);
      if (midi == null) continue;
      zones.push({ midi, file: `${folder}/${f}` });
    }
    zones.sort((a, b) => a.midi - b.midi);
    this.melodicZones.set(folder, zones);
    return zones;
  }

  _noteNameToMidi(name) {
    const m = name.match(/^([A-G])(s|#)?(\d+)$/i) || name.match(/^([A-G])(s)?(\d+)$/i);
    if (!m) return null;
    const letter = m[1].toUpperCase();
    const sharp = (m[2] && (m[2].toLowerCase() === 's' || m[2] === '#')) ? 1 : 0;
    const oct = parseInt(m[3], 10);
    const base = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[letter];
    if (base == null) return null;
    return (oct + 1) * 12 + base + sharp;
  }

  async _listFolder(folder) {
    const key = folder.replace('samples/', '');
    const notes = SAMPLE_MANIFEST[key] || [];
    return notes.map((n) => `${n}.ogg`);
  }

  _pickZonePair(zones, midi) {
    if (!zones?.length) return null;
    if (zones.length === 1 || midi <= zones[0].midi) return { lower: zones[0], upper: null, t: 0 };
    const last = zones[zones.length - 1];
    if (midi >= last.midi) return { lower: last, upper: null, t: 0 };
    for (let i = 0; i < zones.length - 1; i++) {
      const a = zones[i];
      const b = zones[i + 1];
      if (midi >= a.midi && midi <= b.midi) {
        const span = b.midi - a.midi || 1;
        return { lower: a, upper: b, t: (midi - a.midi) / span };
      }
    }
    return { lower: this._pickZone(zones, midi), upper: null, t: 0 };
  }

  _pickZone(zones, midi) {
    let best = zones[0];
    let bestDiff = Infinity;
    for (const z of zones) {
      const d = Math.abs(z.midi - midi);
      if (d < bestDiff) {
        bestDiff = d;
        best = z;
      }
    }
    return best;
  }

  beginSongPrepare(loadToken) {
    this._prepareToken = loadToken;
    if (!this._coreReady) this.prepared = false;
  }

  async _loadPaths(paths, loadToken) {
    if (loadToken !== this._prepareToken) return false;
    const pending = paths.filter((p) => !this._loadedPaths.has(p));
    await Promise.all(pending.map(async (p) => {
      if (loadToken !== this._prepareToken) return;
      await this.loadBuffer(p);
      if (loadToken !== this._prepareToken) return;
      this._loadedPaths.add(p);
      const folder = p.replace(/\/[^/]+\.ogg$/, '');
      if (folder.startsWith('samples/') && folder !== 'samples/drums') {
        await this.loadMelodicZones(folder);
        this._loadedFolders.add(folder);
      }
    }));
    if (loadToken !== this._prepareToken) return false;
    return true;
  }

  /** Drums + acoustic piano once per session (background warm). */
  async ensureCoreSamples(loadToken = this._prepareToken) {
    if (this._coreReady) return true;
    const paths = samplePathsForEvents([], Object.values(DRUM_MAP));
    const ok = await this._loadPaths(paths, loadToken);
    if (!ok) return false;
    this._coreReady = true;
    this._loadedFolders.add('samples/piano');
    return true;
  }

  async ensureSampleFoldersForEvents(events, loadToken = this._prepareToken) {
    const paths = samplePathsForEvents(events, Object.values(DRUM_MAP));
    return this._loadPaths(paths, loadToken);
  }

  /** Preload samples used by this song (parallel fetch + decode). */
  async prepareInstrumentsForEvents(events, loadToken = this._prepareToken) {
    const t0 = typeof performance !== 'undefined' ? performance.now() : 0;
    await this.ensureContext();
    const paths = samplePathsForEvents(events, Object.values(DRUM_MAP));
    const ok = await this._loadPaths(paths, loadToken);
    if (!ok) return false;
    this._coreReady = true;
    this.prepared = true;
    if (t0) this._lastPrepareMs = performance.now() - t0;
    return true;
  }

  _routeToGroup(gainNode, group) {
    gainNode.connect(this.groupNodes[group].dry);
    gainNode.connect(this.groupNodes[group].send);
  }

  _applyHeldEnvelope(gainNode, when, peak, holdSec, releaseSec) {
    scheduleHeldGainEnvelope(gainNode.gain, when, peak, holdSec, releaseSec);
  }

  _startMelodicSample(buf, zoneMidi, targetMidi, when, holdSec, releaseSec, peak, group) {
    const ac = this.ac;
    const rate = Math.pow(2, (targetMidi - zoneMidi) / 12);
    const maxLen = buf.duration / rate;
    const audioLen = Math.min(maxLen, holdSec + releaseSec);
    const src = ac.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = rate;
    const g = ac.createGain();
    this._applyHeldEnvelope(g, when, peak, holdSec, releaseSec);
    src.connect(g);
    this._routeToGroup(g, group);
    try {
      src.start(when, 0, audioLen);
    } catch {
      return null;
    }
    this.activeSources.add(src);
    src.onended = () => this.activeSources.delete(src);
    return src;
  }

  _triggerMelodic(folder, midi, when, duration, velocity, group) {
    const ac = this.ac;
    const zones = this.melodicZones.get(folder);
    if (!zones?.length) return;
    const pair = this._pickZonePair(zones, midi);
    if (!pair) return;

    const peak = scaledGain(velocity, group);
    const hold = duration > 0
      ? Math.max(duration / this.rate, GROUP_MIN_HOLD[group] ?? 0.05)
      : 0.5;
    const release = GROUP_RELEASE[group] ?? 0.4;

    const playOne = (zone, noteMidi, gainScale) => {
      const buf = this.buffers.get(zone.file);
      if (!buf) return;
      if (when < ac.currentTime - 0.02) return;
      this._startMelodicSample(
        buf, zone.midi, noteMidi, when, hold, release, peak * gainScale, group,
      );
    };

    if (pair.upper && pair.t > 0.15 && pair.t < 0.85 && (pair.upper.midi - pair.lower.midi) <= 4) {
      playOne(pair.lower, midi, 1 - pair.t);
      playOne(pair.upper, midi, pair.t);
      return;
    }

    const zone = pair.upper && pair.t >= 0.85 ? pair.upper : pair.lower;
    playOne(zone, midi, 1);
  }

  _triggerDrum(midi, when, duration, velocity) {
    const ac = this.ac;
    const file = drumSampleFile(midi);
    if (!file) return;
    const buf = this.buffers.get(`samples/drums/${file}`);
    if (!buf) return;
    if (when < ac.currentTime - 0.02) return;

    const src = ac.createBufferSource();
    src.buffer = buf;
    const g = ac.createGain();
    const drumMul = DRUM_SAMPLE_GAIN[file] ?? 1;
    const peak = scaledGain(velocity, 'drums') * drumMul;
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0001), when + 0.002);
    src.connect(g);
    this._routeToGroup(g, 'drums');
    try {
      src.start(when, 0);
    } catch {
      return;
    }
    this.activeSources.add(src);
    src.onended = () => this.activeSources.delete(src);
  }

  /** Rare GM programs: soft piano zone fallback (no soundfont bundles). */
  _triggerGm(_program, midi, when, duration, velocity) {
    this._triggerMelodic('samples/piano', midi, when, duration, velocity * 0.55, 'other');
  }

  /**
   * @param {import('@tonejs/midi').Midi} midi
   */
  buildEvents(midi) {
    const events = [];
    for (const track of midi.tracks) {
      const channel = track.channel ?? 0;
      const program = track.instrument?.number ?? 0;
      for (const note of track.notes) {
        const voice = resolveVoice(channel, program);
        const group = voiceToGroup(voice);
        events.push({
          time: note.time,
          duration: note.duration,
          midi: note.midi,
          velocity: note.velocity,
          channel,
          program,
          voice,
          group,
        });
      }
    }
    events.sort((a, b) => a.time - b.time);
    return events;
  }

  schedule(events, startSeconds, endSeconds) {
    if (!this.prepared) return false;
    const ac = this.ac;
    if (!ac) return false;
    this._clearScheduleTimer();
    this._schedQueue = {
      events,
      startSeconds,
      endSeconds,
      index: 0,
      originAc: ac.currentTime + 0.025,
      originSong: startSeconds,
      sid: this.sessionId,
    };
    this._pumpSchedule();
    for (let i = 0; i < 8; i++) this._pumpSchedule();
    this._schedTimer = setInterval(() => this._pumpSchedule(), 100);
    return true;
  }

  _pumpSchedule() {
    const q = this._schedQueue;
    const ac = this.ac;
    if (!q || !ac || q.sid !== this.sessionId) {
      this._clearScheduleTimer();
      return;
    }

    const LOOKAHEAD_AC = 4.5;
    const horizon = ac.currentTime + LOOKAHEAD_AC;

    while (q.index < q.events.length) {
      const ev = q.events[q.index];
      if (ev.time < q.startSeconds - 0.001) {
        q.index += 1;
        continue;
      }
      if (ev.time > q.endSeconds) break;
      const when = q.originAc + (ev.time - q.originSong) / this.rate;
      if (when > horizon) break;
      q.index += 1;
      if (q.sid !== this.sessionId) return;

      const { voice, group } = ev;
      const vel = ev.velocity;

      if (voice.kind === 'drums') {
        this._triggerDrum(ev.midi, when, ev.duration, vel);
        continue;
      }
      if (voice.kind === 'piano') {
        const folder = (voice.sample === 'acoustic' || this.pianoSample === 'acoustic')
          ? 'samples/piano'
          : 'samples/rhodes';
        this._triggerMelodic(folder, ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'bass') {
        this._triggerMelodic('samples/bass', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'trumpet' || voice.kind === 'trombone' || voice.kind === 'tenor_sax' || voice.kind === 'brass_section') {
        this._triggerMelodic(`samples/${voice.kind}`, ev.midi, when, ev.duration, vel, group);
        continue;
      }
      this._triggerGm(ev.program, ev.midi, when, ev.duration, ev.velocity);
    }

    const done = q.index >= q.events.length
      || (q.events[q.index] && q.events[q.index].time > q.endSeconds);
    if (done) this._clearScheduleTimer();
  }
}

export { GROUPS, voiceToGroup };
