(function () {
  if (typeof window.cmsmode === "function") return;

  window.cmsmode = function cmsmode() {
    if (window.__cmsModeActive) {
      return window.__cmsMode;
    }
    if (window.__cmsModeLoading) return;
    window.__cmsModeLoading = true;

    var stub = document.querySelector("script[data-cms-stub]");
    var src = stub && stub.src ? stub.src : "";
    var base = "";
    var versionQuery = "";
    if (src) {
      var qIndex = src.indexOf("?");
      versionQuery = qIndex >= 0 ? src.slice(qIndex) : "";
      base = src.replace(/\/assets\/js\/cmsmode-stub\.js(?:\?.*)?$/, "");
    }

    var css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = base + "/assets/css/cms-mode.css" + versionQuery;
    document.head.appendChild(css);

    var script = document.createElement("script");
    script.src = base + "/assets/js/cms-mode.js" + versionQuery;
    script.onload = function () {
      window.__cmsModeLoading = false;
      if (window.__cmsMode && typeof window.__cmsMode.boot === "function") {
        window.__cmsMode.boot();
      }
    };
    script.onerror = function () {
      window.__cmsModeLoading = false;
      console.error("[cmsmode] Failed to load editor script");
    };
    document.body.appendChild(script);
  };
})();
