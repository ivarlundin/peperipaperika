(function () {
  var DEFAULT_PHRASES = [
    "bröllopsfesten",
    "kickoffen",
    "50-årsfesten",
    "julfesten",
    "företagsfesten",
    "kvällen som aldrig tar slut",
    "oktoberfesten?",
  ];
  var charMs = 85;
  var holdMs = 2800;
  var deleteMs = 48;

  function parsePhrases(root) {
    var raw = root.getAttribute("data-typewriter-phrases");
    if (!raw) return DEFAULT_PHRASES;
    try {
      var parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length) return parsed;
    } catch (err) {
      /* fall through */
    }
    return DEFAULT_PHRASES;
  }

  function sleep(ms) {
    return new Promise(function (resolve) {
      window.setTimeout(resolve, ms);
    });
  }

  function initTypewriter(root) {
    var phrases = parsePhrases(root);
    var once = root.hasAttribute("data-typewriter-once");
    var ghost = root.querySelector(".alt-hero__typewriter-ghost");
    var textEl = root.querySelector("[data-typewriter-text]");
    var caret = root.querySelector(".alt-hero__caret");
    if (!textEl) return;

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

    function finishOnce() {
      root.classList.add("is-complete");
      if (!caret) return;
      caret.classList.add("is-fading");
      return sleep(450).then(function () {
        caret.hidden = true;
      });
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setPhraseText(phrases[0]);
      if (caret) caret.hidden = true;
      root.classList.add("is-complete");
      return;
    }

    if (once) {
      var phrase = phrases[0];
      var charIndex = 0;
      setPhraseText("");

      function tickOnce() {
        if (charIndex < phrase.length) {
          charIndex += 1;
          setPhraseText(phrase.slice(0, charIndex));
          return sleep(charMs).then(tickOnce);
        }
        return finishOnce();
      }

      tickOnce();
      return;
    }

    var phraseIndex = 0;
    var charIndex = phrases[0].length;
    var deleting = false;

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
  }

  document.querySelectorAll("[data-alt-typewriter]").forEach(initTypewriter);
})();
