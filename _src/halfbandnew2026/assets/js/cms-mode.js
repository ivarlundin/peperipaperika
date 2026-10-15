(function () {
  var STORAGE_KEY = "halfbandnew2026-cms-changes-v1";
  var DEFAULT_TYPEWRITER_PHRASES = [
    "bröllopsfesten",
    "kickoffen",
    "50-årsfesten",
    "julfesten",
    "företagsfesten",
  ];

  function assetBase() {
    var stub = document.querySelector("script[data-cms-stub]");
    if (stub && stub.src) {
      return stub.src.replace(/\/assets\/js\/cmsmode-stub\.js(?:\?.*)?$/, "");
    }
    return "";
  }

  function pagePath() {
    return window.location.pathname;
  }

  function sourceFile() {
    var body = document.body;
    return body.getAttribute("data-cms-page-source") || "scripts/build.py";
  }

  function readStore() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { version: 1, changes: {} };
      var parsed = JSON.parse(raw);
      if (!parsed.changes) parsed.changes = {};
      return parsed;
    } catch (e) {
      return { version: 1, changes: {} };
    }
  }

  function writeStore(store) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  }

  function changeCount(store) {
    return Object.keys(store.changes).length;
  }

  function truncate(s, n) {
    s = s || "";
    if (s.length <= n) return s;
    return s.slice(0, n - 1) + "…";
  }

  var manifestPromise = null;

  function loadManifest() {
    if (!manifestPromise) {
      var base = assetBase();
      manifestPromise = fetch(base + "/assets/cms/image-manifest.json")
        .then(function (r) {
          if (!r.ok) throw new Error("manifest");
          return r.json();
        })
        .catch(function () {
          return { images: [] };
        });
    }
    return manifestPromise;
  }

  function findManifestEntry(manifest, currentSrc) {
    if (!currentSrc) return null;
    var images = manifest.images || [];
    var norm = currentSrc.split("?")[0];
    for (var i = 0; i < images.length; i++) {
      var img = images[i];
      var variants = img.variants || {};
      var keys = Object.keys(variants);
      for (var k = 0; k < keys.length; k++) {
        if (variants[keys[k]].split("?")[0] === norm) return img;
      }
      if (img.default && img.default.split("?")[0] === norm) return img;
    }
    return null;
  }

  function applyImageEntry(imgEl, entry, altText) {
    var def = entry.default || (entry.variants && entry.variants.default) || "";
    if (def) imgEl.src = def;
    if (entry.srcset) imgEl.setAttribute("srcset", entry.srcset);
    else imgEl.removeAttribute("srcset");
    if (typeof altText === "string") imgEl.alt = altText;
  }

  function recordChange(store, payload) {
    var id = payload.cmsId;
    var existing = store.changes[id];
    if (!existing) {
      store.changes[id] = payload;
    } else {
      existing.newValue = payload.newValue;
      existing.meta = Object.assign({}, existing.meta, payload.meta || {});
      if (payload.type) existing.type = payload.type;
    }
    writeStore(store);
  }

  function removeChange(store, cmsId) {
    delete store.changes[cmsId];
    writeStore(store);
  }

  function revertElement(el, store) {
    var id = el.getAttribute("data-cms-id");
    if (!id) return;
    var ch = store.changes[id];
    if (!ch) return;
    if (ch.type === "image") {
      var meta = ch.meta || {};
      if (meta.originalSrc) el.src = meta.originalSrc;
      if (meta.originalSrcset === null) el.removeAttribute("srcset");
      else if (typeof meta.originalSrcset === "string") el.setAttribute("srcset", meta.originalSrcset);
      if (typeof meta.originalAlt === "string") el.alt = meta.originalAlt;
    } else if (ch.type === "typewriter") {
      var root = el.closest("[data-alt-typewriter]");
      if (root && ch.meta && ch.meta.originalPhrases) {
        root.setAttribute("data-typewriter-phrases", JSON.stringify(ch.meta.originalPhrases));
        var ghost = root.querySelector(".alt-hero__typewriter-ghost");
        var live = root.querySelector("[data-typewriter-text]");
        if (ghost) ghost.textContent = ch.meta.originalGhost || "";
        if (live) live.textContent = ch.meta.originalPhrases[0] || "";
      }
    } else {
      el.textContent = ch.oldValue;
    }
    removeChange(store, id);
  }

  function applyStoredChanges(store) {
    Object.keys(store.changes).forEach(function (cmsId) {
      var ch = store.changes[cmsId];
      var el = document.querySelector('[data-cms-id="' + cmsId + '"]');
      if (!el) return;
      if (ch.type === "image" && ch.meta && ch.meta.manifestId) {
        loadManifest().then(function (manifest) {
          var entry = (manifest.images || []).find(function (x) {
            return x.id === ch.meta.manifestId;
          });
          if (entry) applyImageEntry(el, entry, ch.newValue);
        });
      } else if (ch.type === "typewriter" && ch.meta && ch.meta.phrases) {
        var root = el.closest("[data-alt-typewriter]") || el;
        root.setAttribute("data-typewriter-phrases", JSON.stringify(ch.meta.phrases));
        var ghost = root.querySelector(".alt-hero__typewriter-ghost");
        var live = root.querySelector("[data-typewriter-text]");
        var longest = ch.meta.phrases.reduce(function (a, b) {
          return a.length >= b.length ? a : b;
        }, ch.meta.phrases[0] || "");
        if (ghost) ghost.textContent = longest;
        if (live) live.textContent = ch.meta.phrases[0] || "";
        root.classList.add("cms-typewriter-paused", "is-complete");
      } else if (ch.type === "text") {
        el.textContent = ch.newValue;
      }
    });
  }

  function exportJson(store) {
    var list = Object.keys(store.changes).map(function (id) {
      return store.changes[id];
    });
    var payload = {
      version: 1,
      site: "halfbandnew2026",
      exportedAt: new Date().toISOString(),
      page: pagePath(),
      changes: list,
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cms-export-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function pauseTypewriter(root) {
    if (!root) return;
    root.classList.add("cms-typewriter-paused", "is-complete");
    var live = root.querySelector("[data-typewriter-text]");
    var caret = root.querySelector(".alt-hero__caret");
    if (caret) caret.hidden = true;
    if (live && !live.textContent) {
      var ghost = root.querySelector(".alt-hero__typewriter-ghost");
      if (ghost) live.textContent = ghost.textContent;
    }
  }

  function parsePhrases(root) {
    var raw = root.getAttribute("data-typewriter-phrases");
    if (!raw) return DEFAULT_TYPEWRITER_PHRASES.slice();
    try {
      var parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length) return parsed.map(String);
    } catch (e) {
      /* ignore */
    }
    return DEFAULT_TYPEWRITER_PHRASES.slice();
  }

  function openTypewriterEditor(root, textEl, store, refreshPanel) {
    pauseTypewriter(root);
    var overlay = document.createElement("div");
    overlay.id = "cms-mode-overlay";
    overlay.className = "cms-ui";
    var box = document.createElement("div");
    box.id = "cms-typewriter-editor";
    box.className = "cms-ui";
    var phrases = parsePhrases(root);
    var originalPhrases = phrases.slice();
    var ghost = root.querySelector(".alt-hero__typewriter-ghost");
    var originalGhost = ghost ? ghost.textContent : "";

    box.innerHTML =
      '<p class="cms-tw-lead">Redigera typewriter-varianter (en rad per fras)</p>' +
      '<textarea id="cms-tw-lines"></textarea>' +
      '<div class="cms-tw-actions">' +
      '<button type="button" class="cms-ui-btn" data-cms-tw-cancel>Avbryt</button>' +
      '<button type="button" class="cms-ui-btn cms-ui-btn--primary" data-cms-tw-save>Spara</button></div>';
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    var ta = box.querySelector("#cms-tw-lines");
    ta.value = phrases.join("\n");

    function close() {
      overlay.remove();
    }

    box.querySelector("[data-cms-tw-cancel]").addEventListener("click", close);
    box.querySelector("[data-cms-tw-save]").addEventListener("click", function () {
      var next = ta.value
        .split("\n")
        .map(function (s) {
          return s.trim();
        })
        .filter(Boolean);
      if (!next.length) return;
      root.setAttribute("data-typewriter-phrases", JSON.stringify(next));
      var longest = next.reduce(function (a, b) {
        return a.length >= b.length ? a : b;
      }, next[0]);
      if (ghost) ghost.textContent = longest;
      var live = root.querySelector("[data-typewriter-text]");
      if (live) live.textContent = next[0];
      pauseTypewriter(root);

      var cmsId = textEl.getAttribute("data-cms-id") || root.getAttribute("data-cms-id");
      if (!cmsId && textEl) {
        cmsId = "cms-tw-" + Math.random().toString(36).slice(2, 9);
        textEl.setAttribute("data-cms-id", cmsId);
        textEl.setAttribute("data-cms-type", "text");
      }
      recordChange(store, {
        cmsId: cmsId,
        page: pagePath(),
        sourceFile: "_src/halfbandnew2026/" + sourceFile(),
        selector: '[data-cms-id="' + cmsId + '"]',
        type: "typewriter",
        oldValue: originalPhrases.join(" | "),
        newValue: next.join(" | "),
        meta: {
          phrases: next,
          originalPhrases: originalPhrases,
          originalGhost: originalGhost,
        },
      });
      refreshPanel();
      close();
    });

    overlay.addEventListener("click", function (ev) {
      if (ev.target === overlay) close();
    });
  }

  function openImagePicker(imgEl, store, refreshPanel) {
    loadManifest().then(function (manifest) {
      var overlay = document.createElement("div");
      overlay.id = "cms-mode-overlay";
      overlay.className = "cms-ui";
      var picker = document.createElement("div");
      picker.id = "cms-mode-picker";
      picker.className = "cms-ui";
      picker.innerHTML =
        '<header class="cms-picker__head">' +
        '<strong class="cms-picker__title">Byt bild</strong>' +
        '<button type="button" class="cms-ui-btn" data-cms-close>Stäng</button></header>' +
        '<div class="cms-picker-grid"></div>';
      overlay.appendChild(picker);
      document.body.appendChild(overlay);

      var grid = picker.querySelector(".cms-picker-grid");
      (manifest.images || []).forEach(function (entry) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "cms-picker-item";
        var thumb = entry.variants["480w"] || entry.variants["800w"] || entry.default;
        btn.innerHTML =
          '<img src="' + thumb + '" alt="" loading="lazy">' +
          '<span class="cms-picker-item__label">' +
          truncate(entry.label, 40) +
          "</span>";
        btn.addEventListener("click", function () {
          var cmsId = imgEl.getAttribute("data-cms-id");
          var oldSrc = imgEl.getAttribute("data-cms-original-src") || imgEl.src;
          var oldSrcset = imgEl.getAttribute("data-cms-original-srcset");
          if (oldSrcset === null) oldSrcset = imgEl.getAttribute("srcset");
          var oldAlt = imgEl.getAttribute("data-cms-original-alt");
          if (oldAlt === null) oldAlt = imgEl.alt;

          applyImageEntry(imgEl, entry, oldAlt);

          var alt = window.prompt("Alt-text (tillgänglighet):", imgEl.alt || "");
          if (alt !== null) imgEl.alt = alt;

          recordChange(store, {
            cmsId: cmsId,
            page: pagePath(),
            sourceFile: "_src/halfbandnew2026/" + sourceFile(),
            selector: '[data-cms-id="' + cmsId + '"]',
            type: "image",
            oldValue: oldSrc,
            newValue: entry.default,
            meta: {
              manifestId: entry.id,
              originalSrc: oldSrc,
              originalSrcset: oldSrcset || null,
              originalAlt: oldAlt,
              alt: imgEl.alt,
            },
          });
          refreshPanel();
          overlay.remove();
        });
        grid.appendChild(btn);
      });

      picker.querySelector("[data-cms-close]").addEventListener("click", function () {
        overlay.remove();
      });
      overlay.addEventListener("click", function (ev) {
        if (ev.target === overlay) overlay.remove();
      });
    });
  }

  function boot() {
    if (window.__cmsModeActive) return;
    window.__cmsModeActive = true;
    document.documentElement.classList.add("cms-mode-active");

    var store = readStore();
    applyStoredChanges(store);

    var panel = document.createElement("div");
    panel.id = "cms-mode-panel";
    panel.className = "cms-ui";
    panel.innerHTML =
      '<p class="cms-panel__title">CMS mode</p>' +
      '<p class="cms-panel__count" data-cms-count></p>' +
      '<ul id="cms-mode-changes"></ul>' +
      '<button type="button" class="cms-ui-btn cms-ui-btn--primary">Export changes</button>' +
      '<button type="button" class="cms-ui-btn cms-ui-btn--ghost">Avsluta CMS mode</button>';
    document.body.appendChild(panel);

    function refreshPanel() {
      panel.querySelector("[data-cms-count]").textContent =
        changeCount(store) + " ändring" + (changeCount(store) === 1 ? "" : "ar");
      var list = panel.querySelector("#cms-mode-changes");
      list.innerHTML = "";
      Object.keys(store.changes).forEach(function (id) {
        var ch = store.changes[id];
        var li = document.createElement("li");
        var label = document.createElement("span");
        label.className = "cms-change-label";
        label.textContent = ch.type + ": " + truncate(ch.newValue, 48);
        var undo = document.createElement("button");
        undo.type = "button";
        undo.className = "cms-ui-btn";
        undo.textContent = "Ångra";
        undo.addEventListener("click", function () {
          var el = document.querySelector('[data-cms-id="' + id + '"]');
          if (el) revertElement(el, store);
          refreshPanel();
        });
        li.appendChild(label);
        li.appendChild(undo);
        list.appendChild(li);
      });
    }

    refreshPanel();

    panel.querySelector(".cms-ui-btn--primary").addEventListener("click", function () {
      exportJson(store);
    });

    panel.querySelector(".cms-ui-btn--ghost").addEventListener("click", function () {
      window.__cmsModeActive = false;
      document.documentElement.classList.remove("cms-mode-active");
      panel.remove();
    });

    document.querySelectorAll("img[data-cms-id]").forEach(function (img) {
      if (!img.getAttribute("data-cms-original-src")) {
        img.setAttribute("data-cms-original-src", img.src);
        img.setAttribute("data-cms-original-srcset", img.getAttribute("srcset") || "");
        img.setAttribute("data-cms-original-alt", img.alt || "");
      }
    });

    document.addEventListener(
      "click",
      function (ev) {
        if (!window.__cmsModeActive) return;
        var t = ev.target;
        if (!(t instanceof Element)) return;
        if (t.closest("#cms-mode-panel") || t.closest("#cms-mode-overlay")) return;

        var img = t.closest("img[data-cms-id]");
        if (img) {
          ev.preventDefault();
          ev.stopPropagation();
          openImagePicker(img, store, refreshPanel);
          return;
        }

        var typeRoot = t.closest("[data-alt-typewriter]");
        var textTarget = t.closest("[data-cms-id][data-cms-type=\"text\"]");
        if (typeRoot && (t.closest("[data-typewriter-text]") || t.closest(".alt-hero__typewriter-ghost"))) {
          ev.preventDefault();
          var textEl = typeRoot.querySelector("[data-typewriter-text]") || typeRoot;
          openTypewriterEditor(typeRoot, textEl, store, refreshPanel);
          return;
        }

        if (!textTarget || textTarget.getAttribute("contenteditable") === "true") return;
        if (typeRoot && typeRoot.contains(textTarget)) return;

        ev.preventDefault();
        var cmsId = textTarget.getAttribute("data-cms-id");
        var oldValue = textTarget.textContent;
        textTarget.setAttribute("contenteditable", "true");
        textTarget.focus();

        function finish() {
          textTarget.removeAttribute("contenteditable");
          var newValue = textTarget.textContent;
          if (newValue !== oldValue) {
            recordChange(store, {
              cmsId: cmsId,
              page: pagePath(),
              sourceFile: "_src/halfbandnew2026/" + sourceFile(),
              selector: '[data-cms-id="' + cmsId + '"]',
              type: "text",
              oldValue: oldValue,
              newValue: newValue,
              meta: { tag: textTarget.tagName.toLowerCase() },
            });
            refreshPanel();
          }
        }

        textTarget.addEventListener("blur", finish, { once: true });
        textTarget.addEventListener("keydown", function (ke) {
          if (ke.key === "Escape") {
            textTarget.textContent = oldValue;
            textTarget.removeAttribute("contenteditable");
            textTarget.blur();
          }
        });
      },
      true
    );
  }

  window.__cmsMode = { boot: boot };
  boot();
})();
