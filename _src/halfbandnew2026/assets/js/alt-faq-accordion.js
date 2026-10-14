(function () {
  var list = document.querySelector("[data-faq]");
  if (!list) return;

  var items = Array.prototype.slice.call(list.querySelectorAll("details.alt-faq__item"));
  if (!items.length) return;

  var DURATION = 280;
  var EASE = "cubic-bezier(0.16, 1, 0.3, 1)";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var cssMotion = false;

  if (!reduced) {
    try {
      cssMotion = CSS.supports("interpolate-size", "allow-keywords");
    } catch (e) {
      cssMotion = false;
    }
    if (cssMotion) {
      list.classList.add("alt-faq--css-motion");
    }
  }

  function closeOthers(except) {
    items.forEach(function (other) {
      if (other === except || !other.open) return;
      if (reduced || cssMotion) {
        other.open = false;
      } else {
        animateClose(other);
      }
    });
  }

  function animateOpen(details) {
    var panel = details.querySelector(".alt-faq__answer");
    if (!panel) {
      details.open = true;
      return;
    }

    details.open = true;
    var endHeight = panel.scrollHeight;
    details.open = false;
    details.open = true;
    details.classList.add("alt-faq__item--animating");
    panel.style.overflow = "hidden";
    panel.style.height = "0";
    panel.style.opacity = "0";

    var anim = panel.animate(
      [
        { height: "0px", opacity: 0 },
        { height: endHeight + "px", opacity: 1 },
      ],
      { duration: DURATION, easing: EASE, fill: "forwards" }
    );

    anim.onfinish = function () {
      panel.style.height = "";
      panel.style.opacity = "";
      panel.style.overflow = "";
      details.classList.remove("alt-faq__item--animating");
    };
  }

  function animateClose(details) {
    var panel = details.querySelector(".alt-faq__answer");
    if (!panel) {
      details.open = false;
      return;
    }

    var startHeight = panel.scrollHeight;
    panel.style.overflow = "hidden";
    panel.style.height = startHeight + "px";
    details.classList.add("alt-faq__item--animating");

    var anim = panel.animate(
      [
        { height: startHeight + "px", opacity: 1 },
        { height: "0px", opacity: 0 },
      ],
      { duration: DURATION, easing: EASE, fill: "forwards" }
    );

    anim.onfinish = function () {
      details.open = false;
      panel.style.height = "";
      panel.style.opacity = "";
      panel.style.overflow = "";
      details.classList.remove("alt-faq__item--animating");
    };
  }

  if (reduced || cssMotion) {
    items.forEach(function (item) {
      item.addEventListener("toggle", function () {
        if (!item.open) return;
        closeOthers(item);
      });
    });
    return;
  }

  items.forEach(function (details) {
    var summary = details.querySelector("summary");
    if (!summary) return;

    summary.addEventListener("click", function (event) {
      event.preventDefault();
      if (details.open) {
        animateClose(details);
        return;
      }
      closeOthers(details);
      animateOpen(details);
    });
  });
})();
