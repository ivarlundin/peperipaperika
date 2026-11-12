(function () {
  "use strict";

  // A major pentatonic across two octaves (pleasant for typing riffs)
  var FREQ = [220.0, 246.94, 277.18, 329.63, 369.99, 440.0, 493.88, 554.37, 659.25, 739.99];

  var REST_WGHT = 240;
  var PEAK_WGHT = 900;
  var EASE_MS = 520;
  var EASE_MS_REDUCED = 80;

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var keys = document.querySelectorAll(".name-key");
  var btnSound = document.getElementById("btn-sound");
  var statusEl = document.getElementById("name-status");
  var hintEl = document.getElementById("name-hint");

  if (!keys.length) return;

  var audioCtx = null;
  var soundOn = false;
  var lastTrigger = 0;

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  function ensureAudio() {
    if (!audioCtx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
  }

  function playNote(noteIndex) {
    if (!soundOn || !audioCtx) return;
    var freq = FREQ[noteIndex];
    if (!freq) return;
    var osc = audioCtx.createOscillator();
    var gain = audioCtx.createGain();
    osc.type = "triangle";
    osc.frequency.value = freq;
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    var t = audioCtx.currentTime;
    var dur = reduced ? 0.12 : 0.22;
    gain.gain.exponentialRampToValueAtTime(0.14, t + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.start(t);
    osc.stop(t + dur + 0.03);
  }

  function easeBack(btn) {
    var ms = reduced ? EASE_MS_REDUCED : EASE_MS;
    window.setTimeout(function () {
      btn.style.fontVariationSettings = '"wght" ' + REST_WGHT;
    }, reduced ? 0 : 40);
    btn.dataset.easeTimer = String(
      window.setTimeout(function () {
        btn.classList.remove("is-easing");
      }, ms + 60)
    );
  }

  function strike(btn) {
    var now = Date.now();
    if (now - lastTrigger < 35) return;
    lastTrigger = now;

    var noteIndex = Number(btn.getAttribute("data-note"));
    if (Number.isNaN(noteIndex)) return;

    var existing = Number(btn.dataset.easeTimer);
    if (existing) window.clearTimeout(existing);

    btn.classList.add("is-easing");
    btn.style.fontVariationSettings = '"wght" ' + PEAK_WGHT;
    playNote(noteIndex);
    easeBack(btn);
  }

  keys.forEach(function (btn) {
    btn.style.fontVariationSettings = '"wght" ' + REST_WGHT;

    btn.addEventListener("pointerenter", function (event) {
      if (event.pointerType === "mouse") strike(btn);
    });

    btn.addEventListener("pointerdown", function (event) {
      if (event.pointerType !== "mouse") {
        event.preventDefault();
        strike(btn);
      }
    });

    btn.addEventListener("click", function (event) {
      if (event.pointerType === "mouse") {
        strike(btn);
      }
    });

    btn.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        strike(btn);
      }
    });
  });

  function setSound(on) {
    soundOn = on;
    btnSound.setAttribute("aria-pressed", on ? "true" : "false");
    btnSound.textContent = on ? "Sound on" : "Sound off";
    if (on) ensureAudio();
    setStatus(on ? "Sound on" : "Sound off");
  }

  if (btnSound) {
    btnSound.addEventListener("click", function () {
      setSound(!soundOn);
    });
  }

  setSound(false);

  if (reduced && hintEl) {
    hintEl.textContent =
      "Focus a letter and press Enter, or tap. Weight snaps quickly; sound stays off until you enable it.";
  }
})();
