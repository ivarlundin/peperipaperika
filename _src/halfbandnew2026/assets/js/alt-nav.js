(function () {
  var header = document.querySelector(".alt-header");
  if (!header) return;

  function setSolid(solid) {
    header.classList.toggle("is-solid", solid);
  }

  function updateFromScroll() {
    if (header.classList.contains("is-open")) return;
    setSolid(window.scrollY > 12);
  }

  updateFromScroll();
  window.addEventListener("scroll", updateFromScroll, { passive: true });
})();
