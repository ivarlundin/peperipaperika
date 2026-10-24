(function () {
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector("[data-nav-toggle]");
  var panel = document.getElementById("mobile-menu");
  var closeBtn = document.querySelector("[data-nav-close]");

  function setOpen(open) {
    if (!toggle || !panel) return;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.documentElement.classList.toggle("nav-open", open);
    panel.hidden = !open;
  }

  if (toggle && panel) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") !== "true";
      setOpen(open);
    });
  }
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      setOpen(false);
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setOpen(false);
  });

  function onScroll() {
    if (!header) return;
    var y = window.scrollY || document.documentElement.scrollTop || 0;
    header.classList.toggle("is-solid", y > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
