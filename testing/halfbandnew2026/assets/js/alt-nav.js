(function () {
  var header = document.querySelector(".alt-header");
  if (!header) return;

  function setSolid(solid) {
    header.classList.toggle("is-solid", solid);
  }

  function updateFromScroll() {
    var mobileMenu = document.querySelector("[data-mobile-menu]");
    if (mobileMenu && !mobileMenu.hidden) return;
    setSolid(window.scrollY > 12);
  }

  updateFromScroll();
  window.addEventListener("scroll", updateFromScroll, { passive: true });
})();
