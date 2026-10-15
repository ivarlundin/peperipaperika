(function () {
  "use strict";

  var SLIDE_MS = 7000;
  var FADE_MS = 900;

  var KEN = [
    { sx: 1.06, sy: 1.06, ex: 1.13, ey: 1.13, tx0: 0, ty0: 0, tx1: -1.4, ty1: -0.9 },
    { sx: 1.06, sy: 1.06, ex: 1.12, ey: 1.12, tx0: 0.6, ty0: 0.4, tx1: -1.1, ty1: -0.6 },
    { sx: 1.06, sy: 1.06, ex: 1.14, ey: 1.14, tx0: -0.5, ty0: 0.2, tx1: 1.0, ty1: -0.8 },
    { sx: 1.06, sy: 1.06, ex: 1.11, ey: 1.11, tx0: 0.3, ty0: -0.3, tx1: -0.9, ty1: 0.5 },
  ];

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function kenTransform(variant, t) {
    var k = KEN[variant % KEN.length];
    var scale = lerp(k.sx, k.ex, t);
    var tx = lerp(k.tx0, k.tx1, t);
    var ty = lerp(k.ty0, k.ty1, t);
    return "scale(" + scale + ") translate3d(" + tx + "%, " + ty + "%, 0)";
  }

  function stopInstance(carousel) {
    var inst = carousel.__svcHeroSlideshow;
    if (!inst) return;
    if (inst.raf) cancelAnimationFrame(inst.raf);
    if (inst.timer) clearTimeout(inst.timer);
    carousel.__svcHeroSlideshow = null;
  }

  function setSlideOpacity(slide, value) {
    slide.style.opacity = String(value);
  }

  function initCarousel(carousel) {
    stopInstance(carousel);
    var slides = carousel.querySelectorAll(".alt-service-hero__slide");
    if (!slides.length) return;

    slides.forEach(function (slide, i) {
      slide.classList.remove("is-active", "is-fading");
      var img = slide.querySelector(".alt-service-hero__img");
      if (img) img.style.transform = kenTransform(i, 0);
      setSlideOpacity(slide, i === 0 ? 1 : 0);
    });
    slides[0].classList.add("is-active");

    if (prefersReducedMotion()) {
      return;
    }

    var count = slides.length;
    var index = 0;
    var phaseStart = performance.now();
    var inst = { raf: 0, timer: 0 };

    function tick(now) {
      var elapsed = now - phaseStart;
      var slide = slides[index];
      var img = slide.querySelector(".alt-service-hero__img");
      var kenT = Math.min(1, elapsed / SLIDE_MS);
      if (img) img.style.transform = kenTransform(index, kenT);

      if (count > 1 && elapsed >= SLIDE_MS) {
        var next = (index + 1) % count;
        var nextSlide = slides[next];
        setSlideOpacity(slide, 0);
        slide.classList.remove("is-active");
        setSlideOpacity(nextSlide, 1);
        nextSlide.classList.add("is-active");
        index = next;
        phaseStart = now;
        var nextImg = nextSlide.querySelector(".alt-service-hero__img");
        if (nextImg) nextImg.style.transform = kenTransform(index, 0);
      }

      inst.raf = requestAnimationFrame(tick);
    }

    inst.raf = requestAnimationFrame(tick);
    carousel.__svcHeroSlideshow = inst;
  }

  function refresh() {
    document.querySelectorAll(".alt-service-hero__carousel").forEach(initCarousel);
  }

  function onReady() {
    refresh();
    window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", refresh);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }

  window.__altServiceHeroSlideshow = { refresh: refresh };
})();
