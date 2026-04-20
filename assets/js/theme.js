// XLNF — theme.js
// Dark/light toggle with localStorage persistence.
// Note: the initial theme is applied by an inline script in each page's <head>
// to prevent FOUC. This module only handles the toggle button.

(function () {
  "use strict";

  const STORAGE_KEY = "xlnf-theme";

  function currentTheme() {
    return document.documentElement.dataset.theme === "light" ? "light" : "dark";
  }

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) {}
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.textContent = theme === "dark" ? "\u2600" : "\u263E"; // ☀ / ☾
      btn.setAttribute("aria-label", `switch to ${theme === "dark" ? "light" : "dark"} theme`);
    }
  }

  function init() {
    const btn = document.getElementById("theme-toggle");
    apply(currentTheme()); // sync button label
    if (!btn) return;
    btn.addEventListener("click", () => {
      const next = currentTheme() === "dark" ? "light" : "dark";
      apply(next);
      if (window.xlnfTrack) window.xlnfTrack("theme_toggle", { to: next });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
