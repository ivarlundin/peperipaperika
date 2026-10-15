(function () {
  var gallery = document.querySelector(".alt-gallery");
  if (!gallery) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var tiles = gallery.querySelectorAll(".alt-gallery__card, .alt-gallery__quote-tile");
  var images = gallery.querySelectorAll(".alt-gallery__card .alt-gallery__ken");

  function revealTile(tile, index) {
    tile.style.setProperty("--alt-gallery-stagger", String(index * 0.06) + "s");
    tile.classList.add("is-in");
  }

  if ("IntersectionObserver" in window) {
    var revealIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var tile = entry.target;
          var index = Number(tile.getAttribute("data-gallery-index") || "0");
          revealTile(tile, index);
          revealIo.unobserve(tile);
          if (tile.classList.contains("alt-gallery__quote-tile")) {
            startQuoteTypewriter(tile);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -4% 0px" }
    );
    tiles.forEach(function (tile, index) {
      tile.setAttribute("data-gallery-index", String(index));
      if (reduceMotion.matches) {
        revealTile(tile, index);
        if (tile.classList.contains("alt-gallery__quote-tile")) {
          startQuoteTypewriter(tile);
        }
      } else {
        revealIo.observe(tile);
      }
    });
  } else {
    tiles.forEach(function (tile, index) {
      revealTile(tile, index);
      if (tile.classList.contains("alt-gallery__quote-tile")) {
        startQuoteTypewriter(tile);
      }
    });
  }

  function startQuoteTypewriter(quoteTile) {
    if (quoteTile.dataset.quoteTyped === "1") return;
    quoteTile.dataset.quoteTyped = "1";

    var live = quoteTile.querySelector("[data-gallery-quote-typewriter]");
    var ghost = quoteTile.querySelector(".alt-gallery__quote-typewriter-ghost");
    if (!live) return;

    var full = (ghost && ghost.textContent) || live.textContent || "";
    full = full.trim();
    if (!full) return;

    if (reduceMotion.matches) {
      live.textContent = full;
      return;
    }

    var charMs = 42;
    var i = 0;
    live.textContent = "";

    var caret = quoteTile.querySelector(".alt-gallery__quote-caret");

    function step() {
      if (i >= full.length) {
        if (caret) caret.style.opacity = "0";
        return;
      }
      i += 1;
      live.textContent = full.slice(0, i);
      window.setTimeout(step, charMs);
    }

    step();
  }

  var parallaxTicking = false;
  var BLEED_RATIO = 0.25;

  function sizeGalleryImages() {
    images.forEach(function (img) {
      var card = img.closest(".alt-gallery__card");
      if (!card) return;
      var cardH = card.clientHeight;
      if (!cardH) return;
      var bleed = cardH * BLEED_RATIO;
      img.style.height = cardH + bleed * 2 + "px";
      img.style.top = -bleed + "px";
      img.style.width = "100%";
    });
  }

  function updateParallax() {
    if (reduceMotion.matches) {
      parallaxTicking = false;
      return;
    }
    images.forEach(function (img) {
      var card = img.closest(".alt-gallery__card");
      if (!card) return;
      var rect = card.getBoundingClientRect();
      var vh = window.innerHeight || 1;
      var center = rect.top + rect.height * 0.5;
      var progress = (center - vh * 0.5) / vh;
      progress = Math.max(-1, Math.min(1, progress));
      var cardH = card.clientHeight || rect.height;
      var maxTravel = Math.max(0, cardH * BLEED_RATIO - 2);
      var yPx = progress * -maxTravel;
      img.style.transform = "translate3d(0," + yPx.toFixed(2) + "px,0)";
    });
    parallaxTicking = false;
  }

  function onScrollParallax() {
    if (reduceMotion.matches) return;
    if (!parallaxTicking) {
      parallaxTicking = true;
      window.requestAnimationFrame(updateParallax);
    }
  }

  function onResizeParallax() {
    sizeGalleryImages();
    onScrollParallax();
  }

  sizeGalleryImages();

  if (!reduceMotion.matches) {
    window.addEventListener("scroll", onScrollParallax, { passive: true });
    window.addEventListener("resize", onResizeParallax);
    updateParallax();
  }

  if ("ResizeObserver" in window) {
    var ro = new ResizeObserver(function () {
      onResizeParallax();
    });
    gallery.querySelectorAll(".alt-gallery__card").forEach(function (card) {
      ro.observe(card);
    });
  }

  reduceMotion.addEventListener("change", function () {
    if (reduceMotion.matches) {
      images.forEach(function (img) {
        img.style.transform = "";
      });
    } else {
      sizeGalleryImages();
      updateParallax();
    }
  });
})();
