(function () {
  var tiles = document.querySelectorAll(".lyssna-video-tile[data-lyssna-video]");
  if (!tiles.length) return;

  function useThumbFallback(img) {
    var fallback = img.getAttribute("data-lyssna-thumb-fallback");
    if (fallback && img.src !== fallback) {
      img.src = fallback;
    }
  }

  document.querySelectorAll("[data-lyssna-thumb-fallback]").forEach(function (img) {
    img.addEventListener("error", function () {
      useThumbFallback(img);
    });
    img.addEventListener("load", function () {
      if (
        img.src.indexOf("i.ytimg.com") !== -1 &&
        img.naturalWidth > 0 &&
        img.naturalWidth < 320
      ) {
        useThumbFallback(img);
      }
    });
  });

  var modal = document.createElement("div");
  modal.className = "lyssna-video-modal";
  modal.hidden = true;
  modal.innerHTML =
    '<div class="lyssna-video-modal__backdrop" data-lyssna-close tabindex="-1"></div>' +
    '<div class="lyssna-video-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="lyssna-video-modal-title">' +
    '<button type="button" class="lyssna-video-modal__close" data-lyssna-close aria-label="Stäng video">' +
    '<span aria-hidden="true">&times;</span></button>' +
    '<p id="lyssna-video-modal-title" class="visually-hidden"></p>' +
    '<div class="lyssna-video-modal__player" data-lyssna-player></div>' +
    "</div>";
  document.body.appendChild(modal);

  var backdrop = modal.querySelector(".lyssna-video-modal__backdrop");
  var dialog = modal.querySelector(".lyssna-video-modal__dialog");
  var closeBtn = modal.querySelector(".lyssna-video-modal__close");
  var titleEl = modal.querySelector("#lyssna-video-modal-title");
  var playerHost = modal.querySelector("[data-lyssna-player]");
  var lastFocus = null;
  var scrollLock = "";

  function focusables() {
    return dialog.querySelectorAll(
      'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
  }

  function trapFocus(event) {
    if (event.key !== "Tab" || modal.hidden) return;
    var nodes = focusables();
    if (!nodes.length) return;
    var first = nodes[0];
    var last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function stopPlayback() {
    playerHost.innerHTML = "";
  }

  function closeModal() {
    if (modal.hidden) return;
    modal.hidden = true;
    document.removeEventListener("keydown", onKeydown);
    document.removeEventListener("keydown", trapFocus);
    stopPlayback();
    document.body.style.overflow = scrollLock;
    if (lastFocus && typeof lastFocus.focus === "function") {
      lastFocus.focus();
    }
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeModal();
    }
  }

  function openModal(videoId, title) {
    lastFocus = document.activeElement;
    titleEl.textContent = title;
    stopPlayback();
    var iframe = document.createElement("iframe");
    iframe.src =
      "https://www.youtube-nocookie.com/embed/" +
      videoId +
      "?autoplay=1&rel=0";
    iframe.title = title;
    iframe.allow =
      "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.allowFullscreen = true;
    playerHost.appendChild(iframe);
    scrollLock = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    modal.hidden = false;
    document.addEventListener("keydown", onKeydown);
    document.addEventListener("keydown", trapFocus);
    closeBtn.focus();
  }

  tiles.forEach(function (tile) {
    tile.addEventListener("click", function () {
      var id = tile.getAttribute("data-lyssna-video");
      var title = tile.getAttribute("data-lyssna-title") || "YouTube-video";
      if (id) openModal(id, title);
    });
  });

  modal.querySelectorAll("[data-lyssna-close]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      closeModal();
    });
  });

  backdrop.addEventListener("click", function () {
    closeModal();
  });
})();
