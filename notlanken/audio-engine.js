import { resolveVoice } from './instruments.js';
import { gmInstrumentName } from './gm-programs.js';

const GROUPS = ['piano', 'bass', 'drums', 'brass', 'other'];

/** Natural release tail after MIDI note-off (seconds). */
const GROUP_RELEASE = {
  piano: 0.42,
  bass: 0.55,
  drums: 0,
  brass: 0.58,
  other: 0.5,
};

/** Minimum held time so staccato MIDI still has body (seconds). */
const GROUP_MIN_HOLD = {
  piano: 0.05,
  bass: 0.07,
  brass: 0.09,
  other: 0.08,
};

/** FluidR3 soundfonts (gleitz) — full multisample, no sparse-zone pitch shift. */
const MELODIC_SOUNDFONT = {
  bass: { name: 'electric_bass_finger', group: 'bass' },
  trumpet: { name: 'trumpet', group: 'brass' },
  trombone: { name: 'trombone', group: 'brass' },
  tenor_sax: { name: 'tenor_sax', group: 'brass' },
  brass_section: { name: 'brass_section', group: 'brass' },
};

const SOUNDFONT_CDN = 'https://gleitz.github.io/midi-js-soundfonts/FluidR3_GM';

/** Per-group gain before velocity (keeps dense arrangements under headroom) */
const GROUP_HEADROOM = {
  piano: 0.32,
  bass: 0.4,
  drums: 0.45,
  brass: 0.35,
  other: 0.32,
};

/** Kick, snare, hats, cymbals only — toms/toys are not played. */
const DRUM_MAP = {
  35: '36-kick.ogg',
  36: '36-kick.ogg',
  37: '38-snare.ogg', // rim → snare
  38: '38-snare.ogg',
  39: '38-snare.ogg', // clap → snare
  42: '42-closed-hat.ogg',
  44: '42-closed-hat.ogg', // pedal hat
  46: '46-open-hat.ogg',
  49: '49-crash.ogg',
  51: '51-ride.ogg',
  53: '51-ride.ogg', // ride bell
};

function drumSampleFile(midi) {
  return DRUM_MAP[midi] || null;
}

const GM_FALLBACK_MAP = {
  violin: 'violin',
  viola: 'violin',
  cello: 'violin',
  contrabass: 'violin',
  string_ensemble_1: 'string_ensemble_1',
  string_ensemble_2: 'string_ensemble_1',
  synth_strings_1: 'synth_strings_1',
  synth_strings_2: 'synth_strings_1',
  acoustic_guitar_nylon: 'acoustic_guitar_nylon',
  acoustic_guitar_steel: 'acoustic_guitar_nylon',
  electric_guitar_jazz: 'acoustic_guitar_nylon',
  flute: 'flute',
  clarinet: 'clarinet',
  oboe: 'flute',
  choir_aahs: 'choir_aahs',
  voice_oohs: 'choir_aahs',
};

const MELODIC_FOLDERS = [
  'samples/piano',
  'samples/rhodes',
];

function voiceToGroup(voice) {
  if (voice.kind === 'piano') return 'piano';
  if (voice.kind === 'bass') return 'bass';
  if (voice.kind === 'drums') return 'drums';
  if (voice.kind === 'trumpet' || voice.kind === 'trombone' || voice.kind === 'tenor_sax' || voice.kind === 'brass_section') {
    return 'brass';
  }
  return 'other';
}

function generateImpulseResponse(ac, duration = 1.6, decay = 2.8) {
  const rate = ac.sampleRate;
  const len = Math.floor(rate * duration);
  const buf = ac.createBuffer(2, len, rate);
  for (let c = 0; c < 2; c++) {
    const ch = buf.getChannelData(c);
    for (let i = 0; i < len; i++) {
      ch[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay) * 0.35;
    }
  }
  return buf;
}

function scaledGain(velocity, group) {
  const v = Math.max(0, Math.min(1, velocity ?? 0.8));
  const head = GROUP_HEADROOM[group] ?? 0.3;
  return v * head;
}

export class AudioEngine {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : baseUrl + '/';
    /** @type {AudioContext | null} */
    this.ac = null;
    this.master = null;
    this.compressor = null;
    this.reverb = null;
    this.reverbWet = null;
    this.reverbDry = null;
    this.groupNodes = {};
    this.buffers = new Map();
    this.gmPlayers = new Map();
    /** @type {Map<string, import('soundfont-player').Instrument>} */
    this.sfPlayers = new Map();
    this.melodicZones = new Map();
    this.sessionId = 0;
    /** @type {Set<AudioBufferSourceNode>} */
    this.activeSources = new Set();
    this.rate = 1;
    this.mixer = {};
    this.prepared = false;
    /** @type {ReturnType<typeof setInterval> | null} */
    this._schedTimer = null;
    this._gmPreloadStarted = false;
    /** @type {null | { events: any[], startSeconds: number, endSeconds: number, index: number, originAc: number, originSong: number, sid: number }} */
    this._schedQueue = null;
    for (const g of GROUPS) {
      this.mixer[g] = { volume: 0.75, mute: false, solo: false, reverbSend: 0.2 };
    }
    this.masterVolume = 0.72;
    this.reverbAmount = 0.12;
    /** Prefer acoustic piano for written charts; Rhodes still available via voice.sample. */
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
      this.reverb = this.ac.createConvolver();
      this.reverb.buffer = generateImpulseResponse(this.ac);
      this.reverbDry.connect(this.master);
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
        send.connect(this.reverb);
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
      this.groupNodes[g].dry.gain.value = vol;
      this.groupNodes[g].send.gain.value = vol * m.reverbSend;
    }
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
    if (this.ac) {
      for (const g of GROUPS) {
        const nodes = this.groupNodes[g];
        if (!nodes) continue;
        nodes.dry.gain.cancelScheduledValues(now);
        nodes.send.gain.cancelScheduledValues(now);
      }
    }
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
    const res = await fetch(this.baseUrl + path);
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
    const m = name.match(/^([A-G])(s)?(\d+)$/i);
    if (!m) return null;
    const letter = m[1].toUpperCase();
    const sharp = m[2] ? 1 : 0;
    const oct = parseInt(m[3], 10);
    const base = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[letter];
    if (base == null) return null;
    return (oct + 1) * 12 + base + sharp;
  }

  async _listFolder(folder) {
    const manifest = {
      piano: ['A1', 'C2', 'Ds2', 'Fs2', 'A2', 'C3', 'Ds3', 'Fs3', 'A3', 'C4', 'Ds4', 'Fs4', 'A4', 'C5', 'Ds5', 'Fs5', 'A5', 'C6'],
      rhodes: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5', 'E5'],
      bass: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'],
      trumpet: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'],
      trombone: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'],
      tenor_sax: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'],
      brass_section: ['C2', 'E2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'],
    };
    const key = folder.replace('samples/', '');
    const notes = manifest[key] || [];
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

  /** Preload buffers so scheduling can run synchronously (no main-thread backlog). */
  async preparePlayback() {
    await this.ensureContext();
    const paths = new Set();
    for (const f of new Set(Object.values(DRUM_MAP))) {
      paths.add(`samples/drums/${f}`);
    }
    for (const folder of MELODIC_FOLDERS) {
      const zones = await this.loadMelodicZones(folder);
      for (const z of zones) paths.add(z.file);
    }
    await Promise.all([...paths].map((p) => this.loadBuffer(p)));
    this.prepared = true;
    if (!this._gmPreloadStarted) {
      this._gmPreloadStarted = true;
      void this._preloadGmFallbacks();
    }
  }

  async _preloadGmFallbacks() {
    const gmNames = new Set(Object.values(GM_FALLBACK_MAP));
    await Promise.all([
      ...[...gmNames].map((name) => this.loadGmPlayer(name).catch(() => null)),
      ...Object.values(MELODIC_SOUNDFONT).map(({ name, group }) =>
        this.loadSoundfontPlayer(name, group).catch(() => null)),
    ]);
  }

  _soundfontUrls(name) {
    const local = new URL(`samples/gm-fallback/${name}-mp3.js`, this.baseUrl).href;
    const remote = `${SOUNDFONT_CDN}/${name}-mp3.js`;
    return [local, remote];
  }

  async loadSoundfontPlayer(name, group) {
    const key = `sf:${name}:${group}`;
    if (this.sfPlayers.has(key)) return this.sfPlayers.get(key);
    const ac = await this.ensureContext();
    const mod = await import('https://esm.sh/soundfont-player@0.12.0');
    const Soundfont = mod.default || mod;
    const out = ac.createGain();
    this._routeToGroup(out, group);
    let player = null;
    for (const url of this._soundfontUrls(name)) {
      try {
        player = await Soundfont.instrument(ac, url, { destination: out, gain: 1 });
        break;
      } catch {
        /* try next URL */
      }
    }
    if (!player) throw new Error(`Soundfont saknas: ${name}`);
    this.sfPlayers.set(key, player);
    return player;
  }

  _sfPlayerForVoice(voiceKind) {
    const spec = MELODIC_SOUNDFONT[voiceKind];
    if (!spec) return null;
    return this.sfPlayers.get(`sf:${spec.name}:${spec.group}`) || null;
  }

  _triggerSoundfontVoice(voiceKind, midi, when, duration, velocity) {
    const spec = MELODIC_SOUNDFONT[voiceKind];
    if (!spec) return false;
    const player = this._sfPlayerForVoice(voiceKind);
    if (!player) return false;
    const group = spec.group;
    const hold = duration > 0
      ? Math.max(duration / this.rate, GROUP_MIN_HOLD[group] ?? 0.08)
      : 0.45;
    const release = GROUP_RELEASE[group] ?? 0.45;
    try {
      const node = player.play(midi, when, {
        duration: hold + release,
        gain: scaledGain(velocity, group),
        attack: 0.012,
        release,
      });
      if (node?.stop) {
        this.activeSources.add(node);
        node.onended = () => this.activeSources.delete(node);
      }
      return true;
    } catch {
      return false;
    }
  }

  _routeToGroup(gainNode, group) {
    gainNode.connect(this.groupNodes[group].dry);
    gainNode.connect(this.groupNodes[group].send);
  }

  _applyHeldEnvelope(gainNode, when, peak, holdSec, releaseSec) {
    const h = Math.max(0.008, holdSec);
    const r = Math.max(0.12, releaseSec);
    gainNode.gain.cancelScheduledValues(when);
    gainNode.gain.setValueAtTime(0.0001, when);
    gainNode.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0001), when + 0.01);
    gainNode.gain.setValueAtTime(peak, when + 0.01);
    gainNode.gain.setValueAtTime(peak, when + h);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, when + h + r);
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
    const peak = scaledGain(velocity, 'drums');
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

  async loadGmPlayer(name) {
    if (this.gmPlayers.has(name)) return this.gmPlayers.get(name);
    const ac = await this.ensureContext();
    const mod = await import('https://esm.sh/soundfont-player@0.12.0');
    const Soundfont = mod.default || mod;
    const file = GM_FALLBACK_MAP[name] || name;
    const url = new URL(`samples/gm-fallback/${file}-mp3.js`, this.baseUrl).href;
    const out = ac.createGain();
    this._routeToGroup(out, 'other');
    const player = await Soundfont.instrument(ac, url, {
      destination: out,
      gain: 0.35,
    });
    this.gmPlayers.set(name, player);
    return player;
  }

  _triggerGm(program, midi, when, duration, velocity) {
    const name = gmInstrumentName(program);
    const fallback = GM_FALLBACK_MAP[name] || 'violin';
    const player = this.gmPlayers.get(fallback);
    if (!player) {
      this._triggerMelodic('samples/piano', midi, when, duration, velocity * 0.6, 'other');
      return;
    }
    try {
      const hold = duration > 0
        ? Math.max(duration / this.rate, GROUP_MIN_HOLD.other)
        : 0.45;
      const release = GROUP_RELEASE.other;
      const node = player.play(midi, when, {
        duration: hold + release,
        gain: scaledGain(velocity, 'other'),
        attack: 0.012,
        release,
      });
      if (node?.stop) {
        this.activeSources.add(node);
        node.onended = () => this.activeSources.delete(node);
      }
    } catch {
      this._triggerMelodic('samples/piano', midi, when, duration, velocity * 0.6, 'other');
    }
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

  /**
   * Lookahead schedule: arm only the next few seconds of notes.
   * Markers-only autokomp can emit 4000+ events; creating that many
   * AudioBufferSourceNodes up front is silent-failure-prone on some browsers.
   */
  schedule(events, startSeconds, endSeconds) {
    if (!this.prepared) return;
    const ac = this.ac;
    if (!ac) return;
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
  }

  _pumpSchedule() {
    const q = this._schedQueue;
    const ac = this.ac;
    if (!q || !ac || q.sid !== this.sessionId) {
      this._clearScheduleTimer();
      return;
    }

    const LOOKAHEAD_AC = 4.5; // seconds of AudioContext time
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
      if (MELODIC_SOUNDFONT[voice.kind]) {
        if (this._triggerSoundfontVoice(voice.kind, ev.midi, when, ev.duration, vel)) continue;
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
