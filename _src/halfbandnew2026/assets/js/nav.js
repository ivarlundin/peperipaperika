(function () {
  var nav = document.querySelector("[data-nav]");
  var toggle = document.querySelector("[data-nav-toggle]");
  var panel = document.querySelector("[data-nav-panel]");
  var backdrop = document.querySelector("[data-nav-backdrop]");
  if (!nav || !toggle || !panel) return;

  var mqDesktop = window.matchMedia("(min-width: 901px)");

  function closeDropdowns() {
    document.querySelectorAll("[data-nav-dropdown]").forEach(function (dd) {
      dd.classList.remove("is-open");
      var btn = dd.querySelector("[data-nav-dropdown-trigger]");
      if (btn) btn.setAttribute("aria-expanded", "false");
    });
  }

  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Stäng meny" : "Öppna meny");
    document.body.classList.toggle("nav-open", open);
    if (backdrop) backdrop.hidden = !open;
    if (!open) closeDropdowns();
  }

  toggle.addEventListener("click", function () {
    setOpen(!nav.classList.contains("is-open"));
  });

  if (backdrop) {
    backdrop.addEventListener("click", function () {
      setOpen(false);
    });
  }

  panel.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });

  document.querySelectorAll("[data-nav-dropdown]").forEach(function (dd) {
    var btn = dd.querySelector("[data-nav-dropdown-trigger]");
    if (!btn) return;

    btn.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      var open = !dd.classList.contains("is-open");
      closeDropdowns();
      if (open) {
        dd.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
      }
    });

    dd.addEventListener("mouseenter", function () {
      if (!mqDesktop.matches) return;
      closeDropdowns();
      dd.classList.add("is-open");
      btn.setAttribute("aria-expanded", "true");
    });

    dd.addEventListener("mouseleave", function () {
      if (!mqDesktop.matches) return;
      dd.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-nav-dropdown]")) closeDropdowns();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (nav.classList.contains("is-open")) setOpen(false);
    else closeDropdowns();
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
