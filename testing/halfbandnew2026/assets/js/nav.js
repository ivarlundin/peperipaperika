(function () {
  var nav = document.querySelector("[data-nav]");
  var toggle = document.querySelector("[data-nav-toggle]");
  var panel = document.querySelector("[data-nav-panel]");
  if (!nav || !toggle || !panel) return;

  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("nav-open", open);
  }

  toggle.addEventListener("click", function () {
    setOpen(!nav.classList.contains("is-open"));
  });

  panel.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") setOpen(false);
  });

  document.querySelectorAll("[data-faq] details").forEach(function (item) {
    item.addEventListener("toggle", function () {
      if (!item.open) return;
      document.querySelectorAll("[data-faq] details").forEach(function (other) {
        if (other !== item) other.open = false;
      });
    });
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
        "Telefon: " + (data.get("phone") || ""),
        "Datum: " + (data.get("date") || ""),
        "Plats: " + (data.get("place") || ""),
        "Typ av tillställning: " + (data.get("type") || ""),
        "",
        data.get("message") || ""
      ];
      var subject = encodeURIComponent("Bokningsförfrågan till Halv Fjorton");
      var body = encodeURIComponent(lines.join("\n"));
      window.location.href = "mailto:halvfjorton@gmail.com?subject=" + subject + "&body=" + body;
    });
  }
})();
