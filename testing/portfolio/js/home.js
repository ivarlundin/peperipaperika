(function () {
  "use strict";

  var MOBILE_MAX = 639;
  var WHITE_ORDER = ["C", "D", "E", "F", "G", "A", "B"];
  var BLACK_AFTER = { C: "C#", D: "D#", F: "F#", G: "G#", A: "A#" };

  var PC_KEYS = {
    a: { off: 0, black: false },
    w: { off: 0, black: true },
    s: { off: 1, black: false },
    e: { off: 1, black: true },
    d: { off: 2, black: false },
    f: { off: 3, black: false },
    t: { off: 3, black: true },
    g: { off: 4, black: false },
    y: { off: 4, black: true },
    h: { off: 5, black: false },
    u: { off: 5, black: true },
    j: { off: 6, black: false },
  };

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var coarse =
    window.matchMedia("(hover: none) and (pointer: coarse)").matches;
  var pianoEl = document.getElementById("piano");
  var hintEl = document.getElementById("piano-hint");
  var statusEl = document.getElementById("piano-status");

  if (!pianoEl) return;

  var audioCtx = null;
  var audioReady = false;
  var baseMidi = 60;
  var octaves = 1;
  var keyByMidi = {};
  var pointerNotes = {};
  var pcHeld = {};
  var pcBaseMidi = 60;
  var resizeTimer;

  function midiToFreq(midi) {
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  function noteName(midi) {
    var names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    var n = names[midi % 12];
    var o = Math.floor(midi / 12) - 1;
    return n + o;
  }

  function octaveCount() {
    var w = window.innerWidth;
    if (w <= MOBILE_MAX) return 1;
    var minWhitePx = 34;
    var maxOct = 7;
    var fit = Math.floor(w / (7 * minWhitePx));
    return Math.min(maxOct, Math.max(2, fit));
  }

  function computeLayout() {
    octaves = octaveCount();
    if (octaves === 1) {
      baseMidi = 60;
      pcBaseMidi = 60;
    } else {
      baseMidi = 48;
      pcBaseMidi = 60;
    }
  }

  function ensureAudio() {
    if (!audioCtx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      return audioCtx.resume().then(function () {
        audioReady = true;
      });
    }
    audioReady = !!audioCtx;
    return Promise.resolve();
  }

  function playNote(midi) {
    if (!audioCtx) return;
    var freq = midiToFreq(midi);
    var t = audioCtx.currentTime;
    var dur = reduced ? 0.35 : 0.55;

    var osc = audioCtx.createOscillator();
    var osc2 = audioCtx.createOscillator();
    var filter = audioCtx.createBiquadFilter();
    var gain = audioCtx.createGain();

    osc.type = "triangle";
    osc2.type = "sine";
    osc.frequency.value = freq;
    osc2.frequency.value = freq * 2;
    osc2.detune.value = 4;

    filter.type = "lowpass";
    filter.frequency.value = Math.min(4000, 600 + freq * 2);
    filter.Q.value = 0.6;

    gain.gain.value = 0.0001;
    osc.connect(filter);
    osc2.connect(filter);
    filter.connect(gain);
    gain.connect(audioCtx.destination);

    gain.gain.exponentialRampToValueAtTime(0.22, t + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.08, t + 0.12);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);

    osc.start(t);
    osc2.start(t);
    osc.stop(t + dur + 0.05);
    osc2.stop(t + dur + 0.05);
  }

  function glowKey(btn) {
    btn.classList.remove("is-lit-fade");
    btn.classList.add("is-lit");
    void btn.offsetWidth;
    btn.classList.add("is-lit-fade");

    if (reduced) {
      window.setTimeout(function () {
        btn.classList.remove("is-lit", "is-lit-fade");
      }, 120);
      return;
    }

    window.setTimeout(function () {
      btn.classList.remove("is-lit");
    }, 40);
    window.setTimeout(function () {
      btn.classList.remove("is-lit-fade");
    }, 520);
  }

  function strikeMidi(midi) {
    var btn = keyByMidi[midi];
    if (!btn) return;
    ensureAudio().then(function () {
      playNote(midi);
      glowKey(btn);
    });
    document.dispatchEvent(new CustomEvent("portfolio:piano-note"));
    if (statusEl) statusEl.textContent = "Played " + noteName(midi);
  }

  function onPointerDown(event) {
    var btn = event.currentTarget;
    event.preventDefault();
    try {
      if (btn.setPointerCapture) btn.setPointerCapture(event.pointerId);
    } catch (err) {
      /* iOS Safari may reject capture */
    }
    var midi = Number(btn.dataset.midi);
    pointerNotes[event.pointerId] = midi;
    strikeMidi(midi);
  }

  function onPointerUp(event) {
    delete pointerNotes[event.pointerId];
  }

  function buildPiano() {
    computeLayout();
    pianoEl.innerHTML = "";
    keyByMidi = {};

    var whitesWrap = document.createElement("div");
    whitesWrap.className = "piano__whites";

    var blacksWrap = document.createElement("div");
    blacksWrap.className = "piano__blacks";
    var whiteIndex = 0;
    var totalWhites = octaves * 7;

    for (var o = 0; o < octaves; o++) {
      var octaveRoot = baseMidi + o * 12;
      for (var wi = 0; wi < WHITE_ORDER.length; wi++) {
        var letter = WHITE_ORDER[wi];
        var midi = octaveRoot + [0, 2, 4, 5, 7, 9, 11][wi];
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "piano-key piano-key--white";
        btn.dataset.midi = String(midi);
        btn.style.setProperty("--white-i", String(whiteIndex));
        btn.setAttribute("aria-label", noteName(midi));
        btn.addEventListener("pointerdown", onPointerDown);
        btn.addEventListener("pointerup", onPointerUp);
        btn.addEventListener("pointercancel", onPointerUp);
        whitesWrap.appendChild(btn);
        keyByMidi[midi] = btn;
        whiteIndex++;

        if (BLACK_AFTER[letter]) {
          var bMidi = midi + 1;
          var black = document.createElement("button");
          black.type = "button";
          black.className = "piano-key piano-key--black";
          black.dataset.midi = String(bMidi);
          black.style.setProperty(
            "--black-pos",
            String((whiteIndex - 1 + 0.68) / totalWhites)
          );
          black.setAttribute("aria-label", noteName(bMidi));
          black.addEventListener("pointerdown", onPointerDown);
          black.addEventListener("pointerup", onPointerUp);
          black.addEventListener("pointercancel", onPointerUp);
          blacksWrap.appendChild(black);
          keyByMidi[bMidi] = black;
        }
      }
    }

    pianoEl.appendChild(whitesWrap);
    pianoEl.appendChild(blacksWrap);
    pianoEl.style.setProperty("--white-count", String(totalWhites));
  }

  function resolvePcKey(code) {
    var spec = PC_KEYS[code];
    if (!spec) return null;
    var midi = pcBaseMidi + spec.off;
    if (spec.black) midi += 1;
    return midi;
  }

  document.addEventListener("keydown", function (event) {
    if (event.repeat) return;
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    var tag = event.target && event.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

    var code = event.key.length === 1 ? event.key.toLowerCase() : "";
    if (!PC_KEYS[code]) return;

    event.preventDefault();
    var midi = resolvePcKey(code);
    pcHeld[code] = midi;
    ensureAudio().then(function () {
      strikeMidi(midi);
    });
  });

  document.addEventListener("keyup", function (event) {
    var code = event.key.length === 1 ? event.key.toLowerCase() : "";
    delete pcHeld[code];
  });

  window.addEventListener("resize", function () {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(buildPiano, 150);
  });

  function configureHint() {
    if (!hintEl) return;
    var touch = hintEl.querySelector(".piano-hint__touch");
    var keys = hintEl.querySelector(".piano-hint__keys");
    if (!touch || !keys) return;
    if (coarse) {
      touch.hidden = false;
      keys.hidden = true;
    } else {
      touch.hidden = true;
      keys.hidden = false;
    }
  }

  function boot() {
    buildPiano();
    configureHint();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
