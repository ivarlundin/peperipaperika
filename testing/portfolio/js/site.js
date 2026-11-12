(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var coarse = window.matchMedia("(hover: none) and (pointer: coarse)").matches;

  function revealIfVisible(node) {
    var rect = node.getBoundingClientRect();
    if (rect.top < window.innerHeight * 1.02 && rect.bottom > -24) {
      node.classList.add("is-revealed");
      return true;
    }
    return false;
  }

  document.querySelectorAll("[data-reveal]").forEach(function (node) {
    if (revealIfVisible(node)) return;
    if (reduced || !("IntersectionObserver" in window)) {
      node.classList.add("is-revealed");
      return;
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px 0px 0px", threshold: 0.01 }
    );
    observer.observe(node);
  });

  function applyDisplayWeight(wght, opsz) {
    document.documentElement.style.setProperty("--wght-display", String(wght));
    if (opsz != null) {
      document.documentElement.style.setProperty("--page-opsz", String(opsz));
    }
  }

  function initPageTitles() {
    var heading = document.getElementById("wght-heading");
    if (!heading) return;

    var baseWght = 900;
    var baseOpsz = 28;
    applyDisplayWeight(baseWght, baseOpsz);

    function onScroll() {
      document.body.classList.toggle("is-scrolled", (window.scrollY || 0) > 8);
      if (reduced) return;
      var y = Math.min(280, window.scrollY || 0);
      applyDisplayWeight(900, Math.round(baseOpsz + y * 0.04));
    }

    function onPointerMove(event) {
      if (reduced || coarse) return;
      var w = window.innerWidth || 1;
      var t = Math.min(1, Math.max(0, event.clientX / w));
      applyDisplayWeight(Math.round(780 + t * 120), null);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    if (!coarse) {
      document.addEventListener("pointermove", onPointerMove, { passive: true });
    }
  }

  function initHeroTitle() {
    var hero = document.getElementById("home-hero-title");
    if (!hero) return;

    var chars = [];
    var text = hero.textContent || "";
    hero.textContent = "";

    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      var span = document.createElement("span");
      span.className = ch === " " ? "vf-char vf-char--space" : "vf-char";
      span.textContent = ch === " " ? "\u00a0" : ch;
      span.style.setProperty("--char-wght", "820");
      hero.appendChild(span);
      if (ch !== " ") chars.push(span);
    }

    function setHeroVars(wght, opsz) {
      document.documentElement.style.setProperty("--hero-wght", String(wght));
      document.documentElement.style.setProperty("--hero-opsz", String(opsz));
    }

    setHeroVars(820, 24);

    function onScroll() {
      if (reduced) return;
      var y = Math.min(320, window.scrollY || 0);
      setHeroVars(Math.round(820 + y * 0.18), Math.round(24 + y * 0.03));
    }

    var raf = 0;
    function onPointerMove(event) {
      if (reduced || coarse || !chars.length) return;
      if (raf) return;
      raf = window.requestAnimationFrame(function () {
        raf = 0;
        var mx = event.clientX;
        var my = event.clientY;
        for (var c = 0; c < chars.length; c++) {
          var rect = chars[c].getBoundingClientRect();
          var cx = rect.left + rect.width / 2;
          var cy = rect.top + rect.height / 2;
          var dist = Math.hypot(mx - cx, my - cy);
          var wght = Math.round(Math.min(900, Math.max(680, 900 - dist * 0.35)));
          chars[c].style.setProperty("--char-wght", String(wght));
        }
      });
    }

    function pulseHero() {
      if (reduced) return;
      hero.classList.add("is-weight-pulse");
      window.setTimeout(function () {
        hero.classList.remove("is-weight-pulse");
      }, 260);
    }

    document.addEventListener("portfolio:piano-note", pulseHero);

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    if (!coarse) {
      document.addEventListener("pointermove", onPointerMove, { passive: true });
    }
  }

  function initMobileNav() {
    var toggle = document.getElementById("nav-toggle");
    var menu = document.getElementById("site-menu");
    var closeBtn = document.getElementById("nav-close");
    var panel = menu && menu.querySelector(".site-menu__panel");
    if (!toggle || !menu || !panel) return;

    var lastFocus = null;

    function focusables() {
      return panel.querySelectorAll(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
    }

    function trapFocus(event) {
      if (menu.hidden || event.key !== "Tab") return;
      var nodes = focusables();
      if (!nodes.length) return;
      var first = nodes[0];
      var last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    function openMenu() {
      lastFocus = document.activeElement;
      menu.hidden = false;
      document.body.classList.add("nav-open");
      toggle.setAttribute("aria-expanded", "true");
      closeBtn.focus();
      document.addEventListener("keydown", trapFocus);
    }

    function closeMenu() {
      menu.hidden = true;
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
      document.removeEventListener("keydown", trapFocus);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    toggle.addEventListener("click", openMenu);
    closeBtn.addEventListener("click", closeMenu);
    menu.addEventListener("click", function (event) {
      if (event.target === menu) closeMenu();
    });
    document.addEventListener("keydown", function (event) {
      if (!menu.hidden && event.key === "Escape") {
        event.preventDefault();
        closeMenu();
      }
    });
    panel.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });
  }

  initPageTitles();
  initHeroTitle();
  initMobileNav();
})();
