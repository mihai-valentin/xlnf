// XLNF — analytics.js
// Thin wrapper over window.posthog. Safe no-op if PostHog isn't initialized yet
// (e.g. placeholder key, blocked by network, etc.). Exposes window.xlnfTrack.

(function () {
  "use strict";

  // `options` is passed through to posthog.capture, e.g. { transport: "sendBeacon",
  // send_instantly: true } for a click that navigates away (see xel.js).
  function track(name, props, options) {
    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(name, props || {}, options);
      }
    } catch (_) {
      // swallow — analytics must never break the UI
    }
  }

  window.xlnfTrack = track;
})();
