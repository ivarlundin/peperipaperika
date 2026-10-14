(function () {
  var body = document.body;
  if (!body.classList.contains("alt-page--home")) return;

  var threshold = 36;
  var mq = window.matchMedia("(max-width: 900px)");

  function updateHeroLogo() {
    if (!mq.matches) {
      body.classList.remove("alt-logo-hero-large");
      return;
    }
    if (body.classList.contains("nav-open")) return;
    body.classList.toggle("alt-logo-hero-large", window.scrollY < threshold);
  }

  updateHeroLogo();
  window.addEventListener("scroll", updateHeroLogo, { passive: true });
  window.addEventListener("alt-nav-closed", updateHeroLogo);
  if (typeof mq.addEventListener === "function") {
    mq.addEventListener("change", updateHeroLogo);
  } else if (typeof mq.addListener === "function") {
    mq.addListener(updateHeroLogo);
  }
})();
