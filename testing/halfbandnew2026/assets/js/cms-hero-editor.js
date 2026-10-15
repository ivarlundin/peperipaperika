(function () {
  var KEN_NAMES = ["alt-hero-ken-a", "alt-hero-ken-b", "alt-hero-ken-c", "alt-hero-ken-d"];

  function heroCmsId(heroKey) {
    return "cms-hero-" + heroKey;
  }

  function escapeAttr(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }

  function manifestEntryById(manifest, id) {
    return (manifest.images || []).find(function (e) {
      return e.id === id;
    });
  }

  function manifestEntryForImg(manifest, img) {
    if (!img) return null;
    var norm = (img.currentSrc || img.src || "").split("?")[0];
    var images = manifest.images || [];
    for (var i = 0; i < images.length; i++) {
      var entry = images[i];
      var variants = entry.variants || {};
      var keys = Object.keys(variants);
      for (var k = 0; k < keys.length; k++) {
        if (variants[keys[k]].split("?")[0] === norm) return entry;
      }
      if (entry.default && entry.default.split("?")[0] === norm) return entry;
    }
    return null;
  }

  function preferHeroManifestEntry(entry, manifest) {
    if (!entry) return entry;
    var base = entry.id.replace(/\.(webp|jpg|jpeg|png)$/i, "");
    if (base.endsWith("-hero")) return entry;
    var heroId = base + "-hero.webp";
    var hero = manifestEntryById(manifest, heroId);
    return hero || entry;
  }

  function srcsetFromEntry(entry) {
    var v = entry.variants || {};
    var order = ["480w", "800w", "1200w", "1600w", "1920w"];
    var parts = [];
    order.forEach(function (w) {
      if (v[w]) parts.push(v[w] + " " + w);
    });
    return parts.join(", ");
  }

  function defaultSrcFromEntry(entry) {
    var v = entry.variants || {};
    return v["1200w"] || v["800w"] || v["1600w"] || entry.default || "";
  }

  function readHeroListFromDom(container, manifest) {
    var list = [];
    var carousel = container.querySelector(".alt-hero__carousel");
    if (carousel) {
      carousel.querySelectorAll(".alt-hero__slide img").forEach(function (img) {
        var entry = manifestEntryForImg(manifest, img);
        list.push({
          manifestId: entry ? entry.id : "",
          alt: img.getAttribute("alt") || "",
        });
      });
      return list;
    }
    var img = container.querySelector(".alt-service-hero__img, img");
    if (img) {
      var entry = manifestEntryForImg(manifest, img);
      list.push({
        manifestId: entry ? entry.id : "",
        alt: img.getAttribute("alt") || "",
      });
    }
    return list;
  }

  function syncSlideAnimations(carousel) {
    var slides = carousel.querySelectorAll(".alt-hero__slide");
    var n = slides.length;
    if (!n) return;
    var cycle = 26;
    slides.forEach(function (slide, i) {
      var delay = (i * cycle) / n;
      slide.style.animationDelay = delay + "s";
      var img = slide.querySelector("img");
      if (img) {
        img.style.animationDelay = delay + "s";
        img.style.animationName = KEN_NAMES[i % KEN_NAMES.length];
        img.style.opacity = "1";
      }
    });
  }

  function buildCarouselSlide(entry, alt, index) {
    var src = defaultSrcFromEntry(entry);
    var srcset = srcsetFromEntry(entry);
    var first = index === 0;
    var loading = first ? "eager" : "lazy";
    var fp = first ? ' fetchpriority="high"' : "";
    var w = entry.id.indexOf("1280") >= 0 ? "1280" : "2400";
    var h = w === "1280" ? "853" : "1600";
    return (
      '<div class="alt-hero__slide">' +
      '<img src="' +
      escapeAttr(src) +
      '"' +
      (srcset ? ' srcset="' + escapeAttr(srcset) + '"' : "") +
      ' sizes="100vw" alt="' +
      escapeAttr(alt) +
      '" width="' +
      w +
      '" height="' +
      h +
      '" loading="' +
      loading +
      '" decoding="async"' +
      fp +
      "></div>"
    );
  }

  function applyHeroListToDom(container, list, manifest) {
    var carousel = container.querySelector(".alt-hero__carousel");
    if (carousel) {
      var html = "";
      list.forEach(function (item, i) {
        var entry = manifestEntryById(manifest, item.manifestId);
        if (!entry) return;
        entry = preferHeroManifestEntry(entry, manifest);
        html += buildCarouselSlide(entry, item.alt || "", i);
      });
      carousel.innerHTML = html;
      syncSlideAnimations(carousel);
      return;
    }
    var img = container.querySelector(".alt-service-hero__img, img");
    if (!img || !list.length) return;
    var entry = manifestEntryById(manifest, list[0].manifestId);
    if (!entry) return;
    var src = defaultSrcFromEntry(entry);
    var srcset = srcsetFromEntry(entry);
    img.src = src;
    if (srcset) img.setAttribute("srcset", srcset);
    else img.removeAttribute("srcset");
    img.alt = list[0].alt || "";
  }

  function openHeroEditor(container, heroKey, store, deps) {
    deps.loadManifest().then(function (manifest) {
      var overlay = document.createElement("div");
      overlay.id = "cms-mode-overlay";
      overlay.className = "cms-ui";
      var panel = document.createElement("div");
      panel.id = "cms-hero-editor";
      panel.className = "cms-ui";
      panel.innerHTML =
        '<header class="cms-picker__head">' +
        "<strong class=\"cms-picker__title\">Hero-bilder</strong>" +
        '<button type="button" class="cms-ui-btn" data-cms-hero-close>Stäng</button></header>' +
        '<p class="cms-hero-editor__hint">Ordna bilder (↑↓), ta bort, eller lägg till från galleriet.</p>' +
        '<ol class="cms-hero-editor__list"></ol>' +
        '<div class="cms-hero-editor__add"><strong>Lägg till</strong></div>' +
        '<div class="cms-picker-grid cms-hero-editor__grid"></div>' +
        '<div class="cms-tw-actions">' +
        '<button type="button" class="cms-ui-btn" data-cms-hero-cancel>Avbryt</button>' +
        '<button type="button" class="cms-ui-btn cms-ui-btn--primary" data-cms-hero-save>Spara</button></div>';

      overlay.appendChild(panel);
      document.body.appendChild(overlay);

      var working = readHeroListFromDom(container, manifest).map(function (item) {
        return { manifestId: item.manifestId, alt: item.alt };
      });
      var original = JSON.parse(JSON.stringify(working));

      var listEl = panel.querySelector(".cms-hero-editor__list");

      function renderList() {
        listEl.innerHTML = "";
        working.forEach(function (item, idx) {
          var entry = manifestEntryById(manifest, item.manifestId);
          var li = document.createElement("li");
          li.className = "cms-hero-editor__item";
          var thumb = entry ? defaultSrcFromEntry(entry) : "";
          li.innerHTML =
            '<img src="' +
            escapeAttr(thumb) +
            '" alt="" class="cms-hero-editor__thumb">' +
            '<span class="cms-hero-editor__label">' +
            escapeAttr((entry && entry.label) || item.manifestId) +
            "</span>" +
            '<input type="text" class="cms-hero-editor__alt" value="' +
            escapeAttr(item.alt) +
            '" aria-label="Alt-text">' +
            '<div class="cms-hero-editor__item-actions">' +
            '<button type="button" class="cms-ui-btn" data-up>↑</button>' +
            '<button type="button" class="cms-ui-btn" data-down>↓</button>' +
            '<button type="button" class="cms-ui-btn" data-remove>Ta bort</button></div>';
          li.querySelector("[data-up]").addEventListener("click", function () {
            if (idx === 0) return;
            var tmp = working[idx - 1];
            working[idx - 1] = working[idx];
            working[idx] = tmp;
            renderList();
          });
          li.querySelector("[data-down]").addEventListener("click", function () {
            if (idx >= working.length - 1) return;
            var tmp = working[idx + 1];
            working[idx + 1] = working[idx];
            working[idx] = tmp;
            renderList();
          });
          li.querySelector("[data-remove]").addEventListener("click", function () {
            if (working.length <= 1) return;
            working.splice(idx, 1);
            renderList();
          });
          li.querySelector(".cms-hero-editor__alt").addEventListener("input", function (ev) {
            working[idx].alt = ev.target.value;
          });
          listEl.appendChild(li);
        });
      }

      var grid = panel.querySelector(".cms-hero-editor__grid");
      (manifest.images || []).forEach(function (entry) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "cms-picker-item";
        var thumb = entry.variants["480w"] || entry.variants["800w"] || entry.default;
        btn.innerHTML =
          '<img src="' + thumb + '" alt="" loading="lazy">' +
          '<span class="cms-picker-item__label">' +
          deps.truncate(entry.label, 36) +
          "</span>";
        btn.addEventListener("click", function () {
          var pick = preferHeroManifestEntry(entry, manifest);
          var alt = window.prompt("Alt-text (valfritt):", "") || "";
          working.push({ manifestId: pick.id, alt: alt });
          renderList();
        });
        grid.appendChild(btn);
      });

      function close() {
        overlay.remove();
      }

      renderList();

      panel.querySelector("[data-cms-hero-close]").addEventListener("click", close);
      panel.querySelector("[data-cms-hero-cancel]").addEventListener("click", close);
      panel.querySelector("[data-cms-hero-save]").addEventListener("click", function () {
        if (!working.length) return;
        applyHeroListToDom(container, working, manifest);
        var cmsId = heroCmsId(heroKey);
        var source =
          heroKey === "home" ? "home/index.html" : "scripts/build.py";
        deps.recordChange(store, {
          cmsId: cmsId,
          page: deps.pagePath(),
          sourceFile: "_src/halfbandnew2026/" + source,
          selector: '[data-cms-hero="' + heroKey + '"]',
          type: "imageList",
          oldValue: JSON.stringify(original),
          newValue: JSON.stringify(working),
          meta: {
            heroKey: heroKey,
            oldList: original,
            newList: working,
            carousel: !!container.querySelector(".alt-hero__carousel"),
          },
        });
        deps.refreshPanel();
        close();
      });

      overlay.addEventListener("click", function (ev) {
        if (ev.target === overlay) close();
      });
    });
  }

  function mountHeroControls(store, deps) {
    document.querySelectorAll("[data-cms-hero]").forEach(function (container) {
      var heroKey = container.getAttribute("data-cms-hero");
      if (!heroKey) return;
      var host =
        container.closest(".alt-hero__media, .alt-service-hero__media, .alt-hero, .alt-service-hero") ||
        container;
      if (host.querySelector(".cms-hero-edit-btn")) return;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cms-hero-edit-btn cms-ui-btn cms-ui-btn--primary";
      btn.textContent = "Hero-bilder";
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        openHeroEditor(container, heroKey, store, deps);
      });
      host.style.position = host.style.position || "relative";
      host.appendChild(btn);
    });
  }

  function applyStoredHeroLists(store, deps) {
    deps.loadManifest().then(function (manifest) {
      Object.keys(store.changes).forEach(function (id) {
        var ch = store.changes[id];
        if (ch.type !== "imageList" || !ch.meta || !ch.meta.newList) return;
        var key = ch.meta.heroKey;
        var container = document.querySelector('[data-cms-hero="' + key + '"]');
        if (!container) return;
        applyHeroListToDom(container, ch.meta.newList, manifest);
      });
    });
  }

  function revertHeroChange(ch, store, deps) {
    if (!ch.meta || !ch.meta.oldList) return;
    var container = document.querySelector('[data-cms-hero="' + ch.meta.heroKey + '"]');
    if (!container) return;
    deps.loadManifest().then(function (manifest) {
      applyHeroListToDom(container, ch.meta.oldList, manifest);
      deps.removeChange(store, ch.cmsId);
      deps.refreshPanel();
    });
  }

  window.__cmsHeroEditor = {
    heroCmsId: heroCmsId,
    mountHeroControls: mountHeroControls,
    applyStoredHeroLists: applyStoredHeroLists,
    revertHeroChange: revertHeroChange,
    applyHeroListToDom: applyHeroListToDom,
    readHeroListFromDom: readHeroListFromDom,
  };
})();
