(function () {
  var year = String(new Date().getFullYear());
  document.querySelectorAll("[data-footer-year]").forEach(function (node) {
    node.textContent = year;
  });
})();
