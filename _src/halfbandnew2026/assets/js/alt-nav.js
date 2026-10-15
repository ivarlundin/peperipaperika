(function () {
  var header = document.querySelector(".alt-header");
  if (!header) return;

  function setSolid(solid) {
    header.classList.toggle("is-solid", solid);
  }

  function updateFromScroll() {
    var mobileMenu = document.querySelector("[data-mobile-menu]");
    if (mobileMenu && !mobileMenu.hidden) return;
    setSolid(window.scrollY > 10);
  }

  function endInitTransition() {
    document.documentElement.classList.remove("alt-header-state-init");
  }

  updateFromScroll();
  window.addEventListener("scroll", updateFromScroll, { passive: true });
  window.addEventListener("alt-nav-closed", updateFromScroll);
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      updateFromScroll();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      function () {
        requestAnimationFrame(endInitTransition);
      },
      { once: true }
    );
  } else {
    requestAnimationFrame(endInitTransition);
  }
})();
