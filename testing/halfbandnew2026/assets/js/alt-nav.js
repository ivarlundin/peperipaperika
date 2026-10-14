(function () {
  var header = document.querySelector(".alt-header");
  if (!header) return;

  function setSolid(solid) {
    header.classList.toggle("is-solid", solid);
  }

  var sentinel = document.querySelector(".alt-header-scroll-sentinel");
  if (sentinel && "IntersectionObserver" in window) {
    setSolid(false);
    new IntersectionObserver(
      function (entries) {
        setSolid(!entries[0].isIntersecting);
      },
      { threshold: 0 }
    ).observe(sentinel);
    return;
  }

  function update() {
    setSolid(window.scrollY > 20);
  }

  update();
  window.addEventListener("scroll", update, { passive: true });
})();
