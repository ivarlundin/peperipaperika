(function () {
  var hero = document.querySelector(".alt-hero");
  if (!hero || !("IntersectionObserver" in window)) return;

  new IntersectionObserver(
    function (entries) {
      var entry = entries[0];
      var visible = entry.isIntersecting && entry.intersectionRatio > 0.05;
      hero.classList.toggle("alt-hero--offscreen", !visible);
    },
    { threshold: [0, 0.05, 0.1] }
  ).observe(hero);
})();
