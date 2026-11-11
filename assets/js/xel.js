// XLNF — xel.js
// Explicit analytics for /xel/ (Xel's room), in the notes.js convention.
//
//   xel_index_view    — /xel/ was opened                    { episodes: <count> }
//   xel_episode_view  — an episode page was opened          { slug, kind }
//   xel_outbound      — a tracked link was clicked           { to, placement, slug }
//       to:        github | guide | youtube | channel | episode  (the link's data-track)
//       placement: episode (an episode page) | catalogue (/xel/)
//       slug:      the nearest [data-slug] — the <article> on an episode page, the
//                  entry <li> on the catalogue; null for the catalogue's channel button

(function () {
  "use strict";

  function track(name, props) {
    if (window.xlnfTrack) window.xlnfTrack(name, props || {});
  }

  function init() {
    var article = document.querySelector("article[data-slug]");
    if (article) {
      track("xel_episode_view", { slug: article.getAttribute("data-slug"), kind: article.getAttribute("data-kind") });
    } else if (document.querySelector(".episodes, .empty")) {
      track("xel_index_view", { episodes: document.querySelectorAll(".episodes > li").length });
    }

    var placement = article ? "episode" : "catalogue";

    // One delegated listener: exactly one event per click, whatever was clicked inside the link.
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[data-track]");
      if (!a) return;
      var owner = a.closest("[data-slug]");
      track("xel_outbound", {
        to: a.getAttribute("data-track"),
        placement: placement,
        slug: owner ? owner.getAttribute("data-slug") : null
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
