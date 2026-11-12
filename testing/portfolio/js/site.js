(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function weightFromX(x) {
    var w = window.innerWidth || 1;
    var t = Math.min(1, Math.max(0, x / w));
    return Math.round(180 + t * 720);
  }

  function applyDisplayWeight(wght) {
    document.documentElement.style.setProperty("--wght-display", String(wght));
  }

  var scrollBase = 400;

  function onPointerMove(event) {
    applyDisplayWeight(weightFromX(event.clientX));
  }

  function onScroll() {
    if (reduced) return;
    var y = window.scrollY || 0;
    var bump = Math.min(180, y * 0.15);
    var base = scrollBase + bump;
    document.documentElement.style.setProperty("--wght-display", String(Math.round(base)));
  }

  var targets = ["wght-role", "wght-heading"];
  var hasTarget = targets.some(function (id) {
    return document.getElementById(id);
  });

  if (hasTarget) {
  applyDisplayWeight(520);
  document.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("scroll", onScroll, { passive: true });
  }
})();
