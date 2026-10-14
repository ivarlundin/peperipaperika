(function () {
  var frames = document.querySelectorAll('iframe[data-tally-src]');
  if (!frames.length) return;

  var loaded = false;

  function loadEmbeds() {
    if (typeof Tally !== "undefined" && Tally.loadEmbeds) {
      Tally.loadEmbeds();
    }
  }

  function loadScript() {
    if (loaded) return;
    loaded = true;
    if (document.querySelector('script[src*="tally.so/widgets/embed.js"]')) {
      loadEmbeds();
      return;
    }
    var script = document.createElement("script");
    script.src = "https://tally.so/widgets/embed.js";
    script.async = true;
    script.onload = loadEmbeds;
    document.head.appendChild(script);
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        if (entries.some(function (entry) {
          return entry.isIntersecting;
        })) {
          loadScript();
          observer.disconnect();
        }
      },
      { rootMargin: "240px 0px" }
    );
    frames.forEach(function (frame) {
      observer.observe(frame);
    });
  } else {
    loadScript();
  }
})();
