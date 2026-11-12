(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function weightFromX(x) {
    var w = window.innerWidth || 1;
    var t = Math.min(1, Math.max(0, x / w));
    return Math.round(200 + t * 680);
  }

  function applyDisplayWeight(wght) {
    document.documentElement.style.setProperty("--wght-display", String(wght));
  }

  var scrollBase = 520;

  function onPointerMove(event) {
    applyDisplayWeight(weightFromX(event.clientX));
  }

  function onScroll() {
    document.body.classList.toggle("is-scrolled", (window.scrollY || 0) > 8);
    if (reduced) return;
    var y = window.scrollY || 0;
    var bump = Math.min(160, y * 0.12);
    applyDisplayWeight(Math.round(scrollBase + bump));
  }

  var weightTargets = ["wght-role", "wght-heading"];
  var hasWeightTarget = weightTargets.some(function (id) {
    return document.getElementById(id);
  });

  if (hasWeightTarget) {
    applyDisplayWeight(scrollBase);
    document.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  if (!reduced && "IntersectionObserver" in window) {
    var nodes = document.querySelectorAll("[data-reveal]");
    if (nodes.length) {
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-revealed");
              observer.unobserve(entry.target);
            }
          });
        },
        { rootMargin: "0px 0px -6% 0px", threshold: 0.08 }
      );
      nodes.forEach(function (node) {
        observer.observe(node);
      });
    }
  } else {
    document.querySelectorAll("[data-reveal]").forEach(function (node) {
      node.classList.add("is-revealed");
    });
  }
})();
