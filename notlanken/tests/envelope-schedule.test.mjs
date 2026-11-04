import {
  noteHoldAndRelease,
  scheduleHeldGainEnvelope,
} from '../audio-engine.js';

function mockGainParam() {
  /** @type {{ kind: string, value: number, time: number }[]} */
  const log = [];
  return {
    log,
    cancelScheduledValues(time) {
      for (let i = log.length - 1; i >= 0; i -= 1) {
        if (log[i].time >= time) log.splice(i, 1);
      }
    },
    setValueAtTime(value, time) {
      log.push({ kind: 'set', value, time });
    },
    exponentialRampToValueAtTime(value, time) {
      log.push({ kind: 'exp', value, time });
    },
    valueAt(t) {
      let v = 0;
      for (const e of log) {
        if (e.time > t) break;
        if (e.kind === 'set') v = e.value;
      }
      return v;
    },
  };
}

const when = 1;
const peak = 0.35;
const param = mockGainParam();
scheduleHeldGainEnvelope(param, when, peak, 0.2, 0.3);

const atOnset = param.valueAt(when + 0.001);
if (atOnset < peak * 0.9) {
  throw new Error(`expected immediate attack at peak, got ${atOnset}`);
}
const attackRamp = param.log.find(
  (e) => e.kind === 'exp' && e.time <= when + 0.015 && e.value > 0.01,
);
if (attackRamp) {
  throw new Error('unexpected exponential ramp during attack (reverse-swell)');
}
const releaseRamp = param.log.find((e) => e.kind === 'exp' && e.time > when + 0.2);
if (!releaseRamp) {
  throw new Error('missing release ramp after hold');
}

const brassShort = noteHoldAndRelease(0.08, 1, 'brass');
if (brassShort.hold > 0.12) {
  throw new Error(`brass hold too long for staccato: ${brassShort.hold}`);
}
if (brassShort.release > 0.35) {
  throw new Error(`brass release too long: ${brassShort.release}`);
}

console.log('envelope-schedule tests OK');
