// XLNF — analytics.js
// Thin wrapper over window.posthog. Safe no-op if PostHog isn't initialized yet
// (e.g. placeholder key, blocked by network, etc.). Exposes window.xlnfTrack.

(function () {
  "use strict";

  function track(name, props) {
    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(name, props || {});
      }
    } catch (_) {
      // swallow — analytics must never break the UI
    }
  }

  window.xlnfTrack = track;
})();
