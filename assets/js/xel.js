// XLNF — xel.js
// Explicit analytics for /xel/ (Xel's room), in the notes.js convention.
//
//   xel_index_view    — /xel/ was opened                    { episodes: <count> }
//   xel_episode_view  — an episode page was opened          { slug, kind }
//   xel_outbound      — a YouTube / channel link was clicked { to, slug }

(function () {
  "use strict";

  function track(name, props) {
    if (window.xlnfTrack) window.xlnfTrack(name, props || {});
  }

  function init() {
    var article = document.querySelector("article[data-slug]");
    var slug = article ? article.getAttribute("data-slug") : null;

    if (article) {
      track("xel_episode_view", { slug: slug, kind: article.getAttribute("data-kind") });
    } else if (document.querySelector(".episodes, .empty")) {
      track("xel_index_view", { episodes: document.querySelectorAll(".episodes > li").length });
    }

    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[data-track]");
      if (a) track("xel_outbound", { to: a.getAttribute("data-track"), slug: slug });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
