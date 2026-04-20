// XLNF — scroll-top.js
// Shows #scroll-top after the user scrolls past a threshold; smooth-scrolls on click.

(function () {
  "use strict";

  const THRESHOLD = 400;

  function init() {
    const btn = document.getElementById("scroll-top");
    if (!btn) return;

    const update = () => {
      const shouldShow = window.scrollY > THRESHOLD;
      btn.hidden = !shouldShow;
    };

    btn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
