(function () {
  var gallery = document.querySelector(".alt-gallery");
  if (!gallery) return;

  var bento = gallery.querySelector(".alt-gallery__bento");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var tiles = gallery.querySelectorAll(".alt-gallery__card, .alt-gallery__quote-tile");
  var images = gallery.querySelectorAll(".alt-gallery__card .alt-gallery__ken");

  var STAGGER_S = 0.14;
  var REVEAL_MS = 1000;
  var revealStarted = false;

  function tilesInVisualOrder() {
    return Array.from(tiles).sort(function (a, b) {
      var ra = a.getBoundingClientRect();
      var rb = b.getBoundingClientRect();
      var rowDelta = ra.top - rb.top;
      if (Math.abs(rowDelta) > 6) return rowDelta;
      return ra.left - rb.left;
    });
  }

  function revealTile(tile, index) {
    tile.style.setProperty("--alt-gallery-stagger", String(index * STAGGER_S) + "s");
    tile.classList.add("is-in");
  }

  function scheduleQuoteTypewriter(quoteTile, index) {
    var delayMs = index * STAGGER_S * 1000 + REVEAL_MS;
    window.setTimeout(function () {
      startQuoteTypewriter(quoteTile);
    }, delayMs);
  }

  function revealGallery() {
    if (revealStarted) return;
    revealStarted = true;
    var ordered = tilesInVisualOrder();
    ordered.forEach(function (tile, index) {
      revealTile(tile, index);
      if (tile.classList.contains("alt-gallery__quote-tile")) {
        scheduleQuoteTypewriter(tile, index);
      }
    });
  }

  if (reduceMotion.matches) {
    tilesInVisualOrder().forEach(function (tile, index) {
      revealTile(tile, index);
      if (tile.classList.contains("alt-gallery__quote-tile")) {
        startQuoteTypewriter(tile);
      }
    });
  } else if ("IntersectionObserver" in window && bento) {
    var revealIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          revealGallery();
          revealIo.unobserve(entry.target);
        });
      },
      { threshold: 0, rootMargin: "0px 0px 15% 0px" }
    );
    revealIo.observe(bento);
  } else {
    revealGallery();
  }

  function quoteFullText(quoteTile) {
    var sr = quoteTile.querySelector(".alt-gallery__quote-sr");
    return ((sr && sr.textContent) || "").trim();
  }

  function buildQuoteCharSpans(quoteTile) {
    var live = quoteTile.querySelector("[data-gallery-quote-typewriter]");
    if (!live || live.dataset.quoteBuilt === "1") {
      return live ? live.querySelectorAll(".alt-gallery__quote-char") : [];
    }

    var full = quoteFullText(quoteTile);
    live.textContent = "";
    live.dataset.quoteBuilt = "1";

    var chars = [];
    for (var c = 0; c < full.length; c += 1) {
      var span = document.createElement("span");
      span.className = "alt-gallery__quote-char";
      span.setAttribute("aria-hidden", "true");
      span.textContent = full.charAt(c);
      live.appendChild(span);
      chars.push(span);
    }
    return chars;
  }

  gallery.querySelectorAll(".alt-gallery__quote-tile").forEach(function (quoteTile) {
    buildQuoteCharSpans(quoteTile);
  });

  function startQuoteTypewriter(quoteTile) {
    if (quoteTile.dataset.quoteTyped === "1") return;
    quoteTile.dataset.quoteTyped = "1";

    var spans = buildQuoteCharSpans(quoteTile);
    if (!spans.length) return;

    if (reduceMotion.matches) {
      spans.forEach(function (span) {
        span.classList.add("is-visible");
      });
      return;
    }

    var charMs = 42;
    var i = 0;

    function step() {
      if (i >= spans.length) return;
      spans[i].classList.add("is-visible");
      i += 1;
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
