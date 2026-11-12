(function () {
  "use strict";

  var shell = document.querySelector("motion-shell.playground");
  if (!shell) return;

  var HUES = [210, 240, 270, 310, 340];
  var index = Math.max(0, HUES.indexOf(Number(shell.getAttribute("data-hue")) || 240));
  if (index === -1) index = 1;

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function applyHue(i) {
    index = ((i % HUES.length) + HUES.length) % HUES.length;
    var hue = HUES[index];
    shell.setAttribute("data-hue", String(hue));
    document.documentElement.style.setProperty("--hue", String(hue));
  }

  applyHue(index);

  function onKeyDown(event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    var target = event.target;
    if (
      target &&
      (target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable)
    ) {
      return;
    }
    if (event.key === "ArrowRight") {
      applyHue(index + 1);
      event.preventDefault();
    } else if (event.key === "ArrowLeft") {
      applyHue(index - 1);
      event.preventDefault();
    }
  }

  document.addEventListener("keydown", onKeyDown);

  var cards = document.querySelectorAll(".card");
  cards.forEach(function (card) {
    card.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        card.classList.toggle("is-pressed");
      }
    });
    card.addEventListener("blur", function () {
      card.classList.remove("is-pressed");
    });
  });

  if (!reducedMotion && window.PointerEvent) {
    var orbA = document.querySelector(".orb--a");
    var orbB = document.querySelector(".orb--b");
    var tick = false;

    function onPointerMove(event) {
      if (tick) return;
      tick = true;
      requestAnimationFrame(function () {
        var x = (event.clientX / window.innerWidth - 0.5) * 24;
        var y = (event.clientY / window.innerHeight - 0.5) * 24;
        if (orbA) orbA.style.transform = "translate(" + x + "px, " + y + "px)";
        if (orbB) orbB.style.transform = "translate(" + -x * 0.6 + "px, " + -y * 0.6 + "px)";
        tick = false;
      });
    }

    document.addEventListener("pointermove", onPointerMove, { passive: true });
  }

  var hint = document.getElementById("play-hint");
  if (hint && reducedMotion) {
    hint.textContent = "Reducerad rörelse är aktiv — färger byts fortfarande med piltangenter.";
  }
})();
