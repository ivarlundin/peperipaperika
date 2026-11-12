(function () {
  "use strict";

  var COLS = 16;
  var ROWS = 8;
  var ROW_CHARS = ["C", "D", "E", "F", "G", "A", "B", "I"];
  var ROW_WEIGHTS = [280, 340, 420, 500, 580, 660, 740, 860];
  var ROW_FREQ = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25];
  var STEP_PATTERN = "IVARLUNDINUXMUSIC";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var gridEl = document.getElementById("seq-grid");
  var stepsEl = document.getElementById("seq-steps");
  var btnPlay = document.getElementById("btn-play");
  var btnStop = document.getElementById("btn-stop");
  var btnClear = document.getElementById("btn-clear");
  var btnSound = document.getElementById("btn-sound");
  var statusEl = document.getElementById("seq-status");
  var hintEl = document.getElementById("seq-hint");
  var section = document.getElementById("sequencer");

  if (!gridEl || !stepsEl) return;

  var cells = [];
  var pattern = [];
  var playing = false;
  var stepIndex = 0;
  var timerId = null;
  var audioCtx = null;
  var soundOn = false;
  var bpm = reduced ? 80 : 112;
  var stepMs = (60 / bpm / 4) * 1000;

  function initPattern() {
    pattern = [];
    for (var r = 0; r < ROWS; r++) {
      var row = [];
      for (var c = 0; c < COLS; c++) row.push(false);
      pattern.push(row);
    }
  }

  function charAt(row, col) {
    var i = (row * COLS + col) % STEP_PATTERN.length;
    return STEP_PATTERN[i];
  }

  function buildGrid() {
    stepsEl.innerHTML = '<span class="sequencer__step-num"></span>';
    for (var c = 0; c < COLS; c++) {
      var num = document.createElement("span");
      num.className = "sequencer__step-num";
      num.textContent = String(c + 1);
      num.dataset.step = String(c);
      stepsEl.appendChild(num);
    }

    gridEl.innerHTML = "";
    cells = [];

    for (var r = 0; r < ROWS; r++) {
      var label = document.createElement("span");
      label.className = "seq-row-label";
      label.textContent = ROW_CHARS[r];
      label.id = "seq-row-" + r;
      gridEl.appendChild(label);

      for (var c = 0; c < COLS; c++) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "seq-cell";
        btn.setAttribute("role", "gridcell");
        btn.setAttribute("aria-label", "Row " + ROW_CHARS[r] + ", step " + (c + 1));
        btn.dataset.row = String(r);
        btn.dataset.col = String(c);
        btn.textContent = charAt(r, c);
        btn.style.fontVariationSettings = '"wght" ' + ROW_WEIGHTS[r];
        btn.addEventListener("click", onCellClick);
        gridEl.appendChild(btn);
        if (!cells[r]) cells[r] = [];
        cells[r][c] = btn;
      }
    }
  }

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  function toggleCell(r, c, force) {
    var next = typeof force === "boolean" ? force : !pattern[r][c];
    pattern[r][c] = next;
    var cell = cells[r][c];
    cell.classList.toggle("is-on", next);
    cell.setAttribute("aria-pressed", next ? "true" : "false");
  }

  function onCellClick(event) {
    var btn = event.currentTarget;
    var r = Number(btn.dataset.row);
    var c = Number(btn.dataset.col);
    toggleCell(r, c);
    if (soundOn && pattern[r][c]) playTone(r, 0.08);
  }

  function ensureAudio() {
    if (!audioCtx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
  }

  function playTone(row, duration) {
    if (!audioCtx || !soundOn) return;
    var osc = audioCtx.createOscillator();
    var gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.value = ROW_FREQ[row];
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    var t = audioCtx.currentTime;
    gain.gain.exponentialRampToValueAtTime(0.12, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + duration);
    osc.start(t);
    osc.stop(t + duration + 0.02);
  }

  function highlightStep(col) {
    var nums = stepsEl.querySelectorAll(".sequencer__step-num");
    nums.forEach(function (el, i) {
      if (i === 0) return;
      el.classList.toggle("is-active", i - 1 === col);
    });
    for (var r = 0; r < ROWS; r++) {
      for (var c = 0; c < COLS; c++) {
        cells[r][c].classList.toggle("is-playhead", c === col);
      }
    }
  }

  function tick() {
    highlightStep(stepIndex);
    for (var r = 0; r < ROWS; r++) {
      if (pattern[r][stepIndex]) {
        cells[r][stepIndex].style.fontVariationSettings =
          '"wght" ' + Math.min(900, ROW_WEIGHTS[r] + 80);
        if (soundOn) playTone(r, 0.1);
      }
    }
    stepIndex = (stepIndex + 1) % COLS;
    if (stepIndex === 0) setStatus("Loop completed");
  }

  function start() {
    if (playing) return;
    playing = true;
    btnPlay.setAttribute("aria-pressed", "true");
    btnPlay.disabled = true;
    btnStop.disabled = false;
    stepIndex = 0;
    setStatus("Playing");
    if (reduced) {
      for (var s = 0; s < COLS; s++) {
        highlightStep(s);
        for (var r = 0; r < ROWS; r++) {
          if (pattern[r][s] && soundOn) playTone(r, 0.08);
        }
      }
      highlightStep(-1);
      stop();
      return;
    }
    tick();
    timerId = window.setInterval(tick, stepMs);
  }

  function stop() {
    playing = false;
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
    btnPlay.disabled = false;
    btnPlay.setAttribute("aria-pressed", "false");
    btnStop.disabled = true;
    highlightStep(-1);
    for (var r = 0; r < ROWS; r++) {
      for (var c = 0; c < COLS; c++) {
        cells[r][c].style.fontVariationSettings = '"wght" ' + ROW_WEIGHTS[r];
      }
    }
    setStatus("Stopped");
  }

  function clearPattern() {
    stop();
    for (var r = 0; r < ROWS; r++) {
      for (var c = 0; c < COLS; c++) toggleCell(r, c, false);
    }
    setStatus("Pattern cleared");
  }

  function setSound(on) {
    soundOn = on;
    section.dataset.sound = on ? "on" : "off";
    btnSound.setAttribute("aria-pressed", on ? "true" : "false");
    btnSound.textContent = on ? "Sound on" : "Sound off";
    if (on) ensureAudio();
    setStatus(on ? "Sound enabled" : "Sound muted");
  }

  btnPlay.addEventListener("click", start);
  btnStop.addEventListener("click", stop);
  btnClear.addEventListener("click", clearPattern);
  btnSound.addEventListener("click", function () {
    setSound(!soundOn);
  });

  gridEl.addEventListener("keydown", function (event) {
    var target = event.target;
    if (!target.classList.contains("seq-cell")) return;
    var r = Number(target.dataset.row);
    var c = Number(target.dataset.col);

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleCell(r, c);
      if (soundOn && pattern[r][c]) playTone(r, 0.08);
    } else if (event.key === "ArrowRight" && c < COLS - 1) {
      event.preventDefault();
      cells[r][c + 1].focus();
    } else if (event.key === "ArrowLeft" && c > 0) {
      event.preventDefault();
      cells[r][c - 1].focus();
    } else if (event.key === "ArrowDown" && r < ROWS - 1) {
      event.preventDefault();
      cells[r + 1][c].focus();
    } else if (event.key === "ArrowUp" && r > 0) {
      event.preventDefault();
      cells[r - 1][c].focus();
    } else if (event.key >= "1" && event.key <= "8") {
      var row = Number(event.key) - 1;
      event.preventDefault();
      cells[row][c].focus();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.target && (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA")) return;
    if (event.key === " " && event.target === document.body) {
      event.preventDefault();
      if (playing) stop();
      else start();
    }
  });

  if (reduced && hintEl) {
    hintEl.textContent =
      "Reduced motion: play advances the full pattern once without a moving playhead. Sound remains opt-in.";
  }

  initPattern();
  buildGrid();
  setSound(false);
})();
