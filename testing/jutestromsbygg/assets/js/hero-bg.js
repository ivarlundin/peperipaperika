(function () {
  function syncHeroBackgrounds() {
    document.querySelectorAll(".home-hero__media[data-cms-hero]").forEach(function (media) {
      var img = media.querySelector("img");
      if (!img || !img.getAttribute("src")) return;
      var src = img.getAttribute("src").split("?")[0];
      media.style.setProperty("--hero-bg-image", 'url("' + src + '")');
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncHeroBackgrounds);
  } else {
    syncHeroBackgrounds();
  }

  document.addEventListener(
    "load",
    function (ev) {
      if (ev.target && ev.target.closest && ev.target.closest(".home-hero__media")) {
        syncHeroBackgrounds();
      }
    },
    true
  );

  try {
    new MutationObserver(syncHeroBackgrounds).observe(document.documentElement, {
      subtree: true,
      attributes: true,
      attributeFilter: ["src"],
    });
  } catch (e) {
    /* ignore */
  }
})();
