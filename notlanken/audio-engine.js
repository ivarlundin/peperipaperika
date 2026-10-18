import { resolveVoice } from './instruments.js';
import { gmInstrumentName } from './gm-programs.js';

const GROUPS = ['piano', 'bass', 'drums', 'brass', 'other'];

/** Per-group gain before velocity (keeps dense arrangements under headroom) */
const GROUP_HEADROOM = {
  piano: 0.28,
  bass: 0.4,
  drums: 0.45,
  brass: 0.35,
  other: 0.32,
};

const DRUM_MAP = {
  35: '36-kick.ogg',
  36: '36-kick.ogg',
  38: '38-snare.ogg',
  41: '41-floor-tom.ogg',
  42: '42-closed-hat.ogg',
  43: '43-high-floor-tom.ogg',
  45: '45-low-tom.ogg',
  46: '46-open-hat.ogg',
  47: '47-mid-tom.ogg',
  48: '47-mid-tom.ogg',
  49: '49-crash.ogg',
  50: '50-high-tom.ogg',
  51: '51-ride.ogg',
};

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
  'samples/bass',
  'samples/trumpet',
  'samples/trombone',
  'samples/tenor_sax',
  'samples/brass_section',
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
    this.melodicZones = new Map();
    this.sessionId = 0;
    /** @type {Set<AudioBufferSourceNode>} */
    this.activeSources = new Set();
    this.rate = 1;
    this.mixer = {};
    this.prepared = false;
    for (const g of GROUPS) {
      this.mixer[g] = { volume: 0.75, mute: false, solo: false, reverbSend: 0.2 };
    }
    this.masterVolume = 0.72;
    this.reverbAmount = 0.12;
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
        dry.connect(this.reverbDry);
        send.connect(this.reverb);
        this.groupNodes[g] = { dry, send };
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
    for (const src of this.activeSources) {
      try {
        src.stop();
      } catch {
        /* already stopped */
      }
    }
    this.activeSources.clear();
    this.sessionId += 1;
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
  }

  _routeToGroup(gainNode, group) {
    gainNode.connect(this.groupNodes[group].dry);
    gainNode.connect(this.groupNodes[group].send);
  }

  _applyNoteEnvelope(gainNode, when, peak, durationSec) {
    const ac = this.ac;
    const d = Math.max(0.03, durationSec);
    const a = 0.004;
    const r = Math.min(0.08, d * 0.35);
    gainNode.gain.cancelScheduledValues(when);
    gainNode.gain.setValueAtTime(0.0001, when);
    gainNode.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0001), when + a);
    gainNode.gain.setValueAtTime(peak, when + Math.max(a, d - r));
    gainNode.gain.exponentialRampToValueAtTime(0.0001, when + d);
  }

  _triggerMelodic(folder, midi, when, duration, velocity, group) {
    const ac = this.ac;
    const zones = this.melodicZones.get(folder);
    if (!zones?.length) return;
    const zone = this._pickZone(zones, midi);
    const buf = this.buffers.get(zone.file);
    if (!buf) return;

    const rate = Math.pow(2, (midi - zone.midi) / 12);
    const maxLen = buf.duration / rate;
    const playDur = duration > 0
      ? Math.min(duration / this.rate, maxLen)
      : Math.min(maxLen, 2.5);

    if (when < ac.currentTime - 0.02) return;

    const src = ac.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = rate;
    const g = ac.createGain();
    const peak = scaledGain(velocity, group);
    this._applyNoteEnvelope(g, when, peak, playDur);
    src.connect(g);
    this._routeToGroup(g, group);
    try {
      src.start(when, 0, playDur);
    } catch {
      return;
    }
    this.activeSources.add(src);
    src.onended = () => this.activeSources.delete(src);
  }

  _triggerDrum(midi, when, duration, velocity) {
    const ac = this.ac;
    const file = DRUM_MAP[midi] || DRUM_MAP[36];
    const buf = this.buffers.get(`samples/drums/${file}`);
    if (!buf) return;
    if (when < ac.currentTime - 0.02) return;

    const len = duration > 0 ? Math.min(duration / this.rate, buf.duration) : buf.duration;
    const src = ac.createBufferSource();
    src.buffer = buf;
    const g = ac.createGain();
    const peak = scaledGain(velocity, 'drums');
    this._applyNoteEnvelope(g, when, peak, len);
    src.connect(g);
    this._routeToGroup(g, 'drums');
    try {
      src.start(when, 0, len);
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
    const player = await Soundfont.instrument(ac, url, {
      destination: this.groupNodes.other.dry,
      gain: 0.35,
    });
    this.gmPlayers.set(name, player);
    return player;
  }

  async _triggerGm(program, midi, when, duration, velocity) {
    const name = gmInstrumentName(program);
    const fallback = GM_FALLBACK_MAP[name] || 'violin';
    try {
      const player = await this.loadGmPlayer(fallback);
      const node = player.play(midi, when, {
        duration: duration / this.rate,
        gain: scaledGain(velocity, 'other'),
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

  schedule(events, startSeconds, endSeconds) {
    if (!this.prepared) return;
    const ac = this.ac;
    if (!ac) return;
    const sid = this.sessionId;
    const now = ac.currentTime + 0.06;
    const gmQueue = [];

    for (const ev of events) {
      if (ev.time < startSeconds - 0.001) continue;
      if (ev.time > endSeconds) continue;
      const when = now + (ev.time - startSeconds) / this.rate;
      if (sid !== this.sessionId) return;

      const { voice, group } = ev;
      const vel = ev.velocity;

      if (voice.kind === 'drums') {
        this._triggerDrum(ev.midi, when, ev.duration, vel);
        continue;
      }
      if (voice.kind === 'piano') {
        this._triggerMelodic('samples/piano', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'bass') {
        this._triggerMelodic('samples/bass', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'trumpet') {
        this._triggerMelodic('samples/trumpet', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'trombone') {
        this._triggerMelodic('samples/trombone', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'tenor_sax') {
        this._triggerMelodic('samples/tenor_sax', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      if (voice.kind === 'brass_section') {
        this._triggerMelodic('samples/brass_section', ev.midi, when, ev.duration, vel, group);
        continue;
      }
      gmQueue.push(ev);
    }

    if (gmQueue.length && sid === this.sessionId) {
      void Promise.all(
        gmQueue.map((ev) => {
          const when = now + (ev.time - startSeconds) / this.rate;
          return this._triggerGm(ev.program, ev.midi, when, ev.duration, ev.velocity);
        }),
      );
    }
  }
}

export { GROUPS, voiceToGroup };
