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
      var hero = document.createElement("script");
      hero.src = base + "/assets/js/cms-hero-editor.js" + versionQuery;
      hero.onload = function () {
        window.__cmsModeLoading = false;
        if (window.__cmsMode && typeof window.__cmsMode.boot === "function") {
          window.__cmsMode.boot();
        }
      };
      hero.onerror = function () {
        window.__cmsModeLoading = false;
        console.error("[cmsmode] Failed to load hero editor script");
        if (window.__cmsMode && typeof window.__cmsMode.boot === "function") {
          window.__cmsMode.boot();
        }
      };
      document.body.appendChild(hero);
    };
    script.onerror = function () {
      window.__cmsModeLoading = false;
      console.error("[cmsmode] Failed to load editor script");
    };
    document.body.appendChild(script);
  };

  function mountEditFab() {
    if (document.getElementById("jb-cms-edit-fab")) return;
    var btn = document.createElement("button");
    btn.id = "jb-cms-edit-fab";
    btn.type = "button";
    btn.className = "jb-cms-edit-fab";
    btn.textContent = "Edit";
    btn.setAttribute("aria-label", "Redigera innehåll (CMS-läge)");
    btn.addEventListener("click", function () {
      btn.hidden = true;
      window.cmsmode();
    });
    document.body.appendChild(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountEditFab);
  } else {
    mountEditFab();
  }
})();
