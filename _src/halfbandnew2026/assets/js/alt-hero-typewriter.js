(function () {
  var root = document.querySelector("[data-alt-typewriter]");
  if (!root) return;

  var ghost = root.querySelector(".alt-hero__typewriter-ghost");
  var textEl = root.querySelector("[data-typewriter-text]");
  var caret = root.querySelector(".alt-hero__caret");
  if (!textEl) return;

  var phrases = [
    "bröllopsfesten",
    "kickoffen",
    "50-årsfesten",
    "julfesten",
    "företagsfesten",
  ];
  var charMs = 85;
  var holdMs = 2800;
  var deleteMs = 48;

  var longestPhrase = phrases.reduce(function (a, b) {
    return a.length >= b.length ? a : b;
  }, phrases[0]);

  if (ghost) {
    ghost.textContent = longestPhrase;
  }

  function setPhraseText(value) {
    textEl.textContent = value;
    if (caret) {
      caret.hidden = value.length === 0;
    }
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setPhraseText(phrases[0]);
    if (caret) caret.hidden = true;
    return;
  }

  var phraseIndex = 0;
  var charIndex = phrases[0].length;
  var deleting = false;

  function sleep(ms) {
    return new Promise(function (resolve) {
      window.setTimeout(resolve, ms);
    });
  }

  function tick() {
    var phrase = phrases[phraseIndex];

    if (!deleting) {
      if (charIndex < phrase.length) {
        charIndex += 1;
        setPhraseText(phrase.slice(0, charIndex));
        return sleep(charMs).then(tick);
      }
      return sleep(holdMs).then(function () {
        deleting = true;
        return tick();
      });
    }

    if (charIndex > 0) {
      charIndex -= 1;
      setPhraseText(phrase.slice(0, charIndex));
      return sleep(deleteMs).then(tick);
    }

    deleting = false;
    phraseIndex = (phraseIndex + 1) % phrases.length;
    setPhraseText("");
    return sleep(charMs).then(tick);
  }

  setPhraseText(phrases[0]);
  charIndex = phrases[0].length;
  sleep(holdMs).then(function () {
    deleting = true;
    tick();
  });
})();
