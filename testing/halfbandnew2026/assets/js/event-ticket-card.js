(function () {
  var root = document.querySelector("[data-event-ticket]");
  if (!root) return;

  var badge = root.querySelector("[data-event-badge]");
  var countdown = root.querySelector("[data-event-countdown]");
  if (!badge || !countdown) return;

  var startMs = Date.parse(root.getAttribute("data-event-start") || "");
  var endMs = Date.parse(root.getAttribute("data-event-end") || "");
  if (!startMs || !endMs) return;

  function update() {
    var now = Date.now();
    if (now > endMs) {
      badge.textContent = "Har varit";
      countdown.hidden = true;
      root.classList.add("event-ticket--past");
      return;
    }

    badge.textContent = "Kommande";
    countdown.hidden = false;

    var dayMs = 86400000;
    var days = Math.ceil((startMs - now) / dayMs);
    if (days > 1) {
      countdown.textContent = days + " dagar kvar";
    } else if (days === 1) {
      countdown.textContent = "1 dag kvar";
    } else {
      countdown.textContent = "Idag";
    }
  }

  update();
  window.setInterval(update, 60000);
})();
