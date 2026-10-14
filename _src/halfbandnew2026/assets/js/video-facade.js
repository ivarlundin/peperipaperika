(function () {
  document.querySelectorAll("[data-video-facade]").forEach(function (wrap) {
    var id = wrap.getAttribute("data-video-facade");
    if (!id) return;
    var btn = wrap.querySelector(".video-facade__play");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var title = wrap.getAttribute("data-video-title") || "YouTube-video";
      var iframe = document.createElement("iframe");
      iframe.src =
        "https://www.youtube-nocookie.com/embed/" +
        id +
        "?autoplay=1";
      iframe.title = title;
      iframe.allow =
        "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.allowFullscreen = true;
      iframe.loading = "lazy";
      wrap.innerHTML = "";
      wrap.classList.add("is-playing");
      wrap.appendChild(iframe);
    });
  });
})();
