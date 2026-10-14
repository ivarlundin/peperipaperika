(function () {
  var nodes = document.querySelectorAll("[data-alt-section-typewriter]");
  if (!nodes.length) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var charMs = 85;

  function lockTypewriterHeight(root, ghost) {
    if (!ghost) return;
    var h = ghost.offsetHeight;
    if (h > 0) {
      root.style.minHeight = h + "px";
    }
  }

  function runTypewriter(root) {
    var ghost = root.querySelector(".alt-section-typewriter__ghost");
    var textEl = root.querySelector("[data-section-typewriter-text]");
    var caret = root.querySelector(".alt-section-typewriter__caret");
    if (!ghost || !textEl) return;

    var full = ghost.textContent || "";
    lockTypewriterHeight(root, ghost);

    if (reduceMotion) {
      textEl.textContent = full;
      root.classList.add("is-complete");
      if (caret) caret.hidden = true;
      return;
    }

    var index = 0;
    textEl.textContent = "";

    function tick() {
      if (index < full.length) {
        index += 1;
        textEl.textContent = full.slice(0, index);
        window.setTimeout(tick, charMs);
        return;
      }
      root.classList.add("is-complete");
      lockTypewriterHeight(root, ghost);
      if (caret) caret.hidden = true;
    }

    tick();
  }

  function prepare(node) {
    var ghost = node.querySelector(".alt-section-typewriter__ghost");
    if (!ghost) return;
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        lockTypewriterHeight(node, ghost);
      });
    } else {
      lockTypewriterHeight(node, ghost);
    }
  }

  nodes.forEach(prepare);

  if (reduceMotion || typeof IntersectionObserver === "undefined") {
    nodes.forEach(runTypewriter);
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        runTypewriter(entry.target);
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.15 }
  );

  nodes.forEach(function (node) {
    observer.observe(node);
  });
})();
