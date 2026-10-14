(function () {
  var header = document.querySelector(".alt-header");
  if (!header) return;

  function update() {
    header.classList.toggle("is-solid", window.scrollY > 20);
  }

  update();
  window.addEventListener("scroll", update, { passive: true });
})();
