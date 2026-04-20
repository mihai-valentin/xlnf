// XLNF — decoder.js
// Picks a random backronym for #xlnf-decoder on load; click to re-roll.

(function () {
  "use strict";

  const BACKRONYMS = [
    "Xtremely Lightweight Nonsense Factory",
    "eXperimental Lab for Nebulous Futures",
    "Xenomorphic Linear Noise Framework",
    "eXecutable Late-Night Fever-dreams",
    "Xylophone-Loving Neural Farmers",
    "eXtensible Ledger of Null Functions",
    "eXiled Linux Ninjas Federation",
    "Xerox Like Not Found",
    "eXtremely Late Nightly Failures",
    "Xanthippe's Last Noble Fight",
    "eXception Lives Next Friday",
    "eXtraterrestrial Lambda Noodle Factory",
    "eXit Loop Never Finishes",
    "eXclusive League of Napping Freelancers",
    "eXpired License, Needs Funding",
    "Xylocaine for Legacy Node Frontends",
    "eXhausted Laptop, Need Flatwhite",
    "eXpert Level Null Feedback",
    "Xi'an Lorry of Numbered Failures",
    "eXploratory Lightbulb-Naming Foundation",
    "eXcessively Loud Napping Facility",
    "eXact Location: Not Found",
    "eXtra-Large Number Factory",
    "eXpedition Leader, Not Found",
    "eXistential Loops, Nested Forever",
    "eXciting Logs, No Flamegraph",
    "eXplosive Launch, No Fallback",
    "Xtra-terrestrial Laboratory for Novel Fauna",
    "eXhaust Leak, Needs Fixing",
    "eXhibit L: Not Functional",
    "Xylem-Level Network Fluidity",
    "eXtensive Logging, Negligible Facts",
    "eXhumed Legacy Node Framework",
    "eXotic Linguistic Noise Factory",
    "eXpensive Lunches, Negligible Features",
    "eXperimental License to Not Ship",
    "eXemplary Level of Nothing Finished",
    "Xenon-Lit Neon Futurism",
    "eXit: Leave Nothing Finished",
    "eXtract, Load, Never Finish",
  ];

  function pickIndex(excluding) {
    if (BACKRONYMS.length <= 1) return 0;
    let i = Math.floor(Math.random() * BACKRONYMS.length);
    if (i === excluding) i = (i + 1) % BACKRONYMS.length;
    return i;
  }

  function render(el, index) {
    el.textContent = BACKRONYMS[index];
    el.dataset.index = String(index);
    el.setAttribute("title", "click to re-roll");
  }

  function init() {
    const el = document.getElementById("xlnf-decoder");
    if (!el) return;
    render(el, pickIndex(-1));
    const reroll = () => {
      const prev = Number(el.dataset.index);
      render(el, pickIndex(Number.isNaN(prev) ? -1 : prev));
      if (window.xlnfTrack) window.xlnfTrack("decoder_reroll");
    };
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.addEventListener("click", reroll);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        reroll();
      }
    });
  }

  // Expose the full list for decoder.html to render.
  window.XLNF_BACKRONYMS = BACKRONYMS;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
