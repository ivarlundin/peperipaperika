(function () {
  var mobileMenu = document.querySelector("[data-mobile-menu]");
  var toggle = document.querySelector("[data-nav-toggle]");
  if (!mobileMenu || !toggle) return;

  var panel = mobileMenu.querySelector("[data-nav-panel]");
  var closeButtons = document.querySelectorAll("[data-nav-close]");
  var mqDesktop = window.matchMedia("(min-width: 901px)");
  var scrollLockY = 0;
  var header = document.querySelector(".alt-header");
  var menuMotionMs = 320;
  var closeTimer = null;

  function isMobileNav() {
    return !mqDesktop.matches;
  }

  function scrollbarGap() {
    return Math.max(0, window.innerWidth - document.documentElement.clientWidth);
  }

  function lockPageScroll() {
    if (!isMobileNav()) return;
    scrollLockY = window.scrollY || window.pageYOffset || 0;
    var gap = scrollbarGap();
    document.documentElement.classList.add("alt-page-nav-lock");
    document.body.classList.add("nav-open");
    if (gap > 0) {
      document.body.style.paddingRight = gap + "px";
      if (header) header.style.paddingRight = gap + "px";
    }
    document.body.style.top = "-" + scrollLockY + "px";
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
  }

  function unlockPageScroll() {
    if (!document.body.classList.contains("nav-open")) return;
    document.body.classList.remove("nav-open");
    document.documentElement.classList.remove("alt-page-nav-lock");
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    document.body.style.paddingRight = "";
    if (header) header.style.paddingRight = "";
    window.scrollTo(0, scrollLockY);
  }

  function menuIsOpen() {
    return mobileMenu.classList.contains("mobile-menu--open");
  }

  function runAfterPaint(callback) {
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        void mobileMenu.offsetHeight;
        callback();
      });
    });
  }

  function closeDropdowns(scope) {
    (scope || document).querySelectorAll("[data-nav-dropdown]").forEach(function (dd) {
      dd.classList.remove("is-open");
      var btn = dd.querySelector("[data-nav-dropdown-trigger]");
      if (btn) btn.setAttribute("aria-expanded", "false");
    });
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function finishMenuClose() {
    mobileMenu.hidden = true;
    mobileMenu.setAttribute("aria-hidden", "true");
    unlockPageScroll();
    closeDropdowns(mobileMenu);
  }

  function setOpen(open) {
    if (!isMobileNav() && open) return;
    if (open === menuIsOpen()) return;

    if (closeTimer) {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    }

    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Stäng meny" : "Öppna meny");

    if (open) {
      mobileMenu.hidden = false;
      mobileMenu.setAttribute("aria-hidden", "false");
      mobileMenu.classList.remove("mobile-menu--open");
      lockPageScroll();

      if (prefersReducedMotion()) {
        mobileMenu.classList.add("mobile-menu--open");
        return;
      }

      runAfterPaint(function () {
        mobileMenu.classList.add("mobile-menu--open");
      });
      return;
    }

    mobileMenu.classList.remove("mobile-menu--open");
    mobileMenu.setAttribute("aria-hidden", "true");

    if (prefersReducedMotion()) {
      finishMenuClose();
      return;
    }

    var onEnd = function (event) {
      if (event.target !== mobileMenu || event.propertyName !== "opacity") return;
      mobileMenu.removeEventListener("transitionend", onEnd);
      if (closeTimer) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      finishMenuClose();
    };

    mobileMenu.addEventListener("transitionend", onEnd);
    closeTimer = window.setTimeout(function () {
      mobileMenu.removeEventListener("transitionend", onEnd);
      closeTimer = null;
      finishMenuClose();
    }, menuMotionMs + 80);
  }

  toggle.addEventListener("click", function () {
    setOpen(!menuIsOpen());
  });

  closeButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setOpen(false);
    });
  });

  if (panel) {
    panel.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setOpen(false);
      });
    });
  }

  mobileMenu.querySelectorAll("[data-nav-dropdown]").forEach(function (dd) {
    var btn = dd.querySelector("[data-nav-dropdown-trigger]");
    if (!btn) return;

    btn.addEventListener("click", function (event) {
      if (mqDesktop.matches) return;
      event.preventDefault();
      event.stopPropagation();
      var open = !dd.classList.contains("is-open");
      closeDropdowns(mobileMenu);
      if (open) {
        dd.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
      }
    });
  });

  document.querySelectorAll(".alt-header [data-nav-dropdown]").forEach(function (dd) {
    var btn = dd.querySelector("[data-nav-dropdown-trigger]");
    if (!btn) return;

    btn.addEventListener("mouseenter", function () {
      if (!mqDesktop.matches) return;
      closeDropdowns(document.querySelector(".alt-header"));
      dd.classList.add("is-open");
      btn.setAttribute("aria-expanded", "true");
    });

    dd.addEventListener("mouseleave", function () {
      if (!mqDesktop.matches) return;
      dd.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    });

    btn.addEventListener("click", function (event) {
      if (!mqDesktop.matches) return;
      event.preventDefault();
      event.stopPropagation();
      var open = !dd.classList.contains("is-open");
      closeDropdowns(document.querySelector(".alt-header"));
      if (open) {
        dd.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
      }
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-nav-dropdown]")) {
      closeDropdowns();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (menuIsOpen()) setOpen(false);
    else closeDropdowns();
  });

  mqDesktop.addEventListener("change", function () {
    if (mqDesktop.matches) setOpen(false);
  });

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    document.querySelectorAll("[data-reveal]").forEach(function (node) {
      io.observe(node);
    });
  } else {
    document.querySelectorAll("[data-reveal]").forEach(function (node) {
      node.classList.add("is-in");
    });
  }

  var form = document.querySelector("[data-mailto-form]");
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var data = new FormData(form);
      var lines = [
        "Namn: " + (data.get("name") || ""),
        "E-post: " + (data.get("email") || ""),
        "Datum: " + (data.get("date") || ""),
        "Plats: " + (data.get("place") || ""),
        "Typ av tillställning: " + (data.get("type") || ""),
        "",
        data.get("message") || "",
      ];
      var subject = encodeURIComponent("Bokningsförfrågan till Halv Fjorton");
      var body = encodeURIComponent(lines.join("\n"));
      window.location.href = "mailto:halvfjorton@gmail.com?subject=" + subject + "&body=" + body;
    });
  }
})();
