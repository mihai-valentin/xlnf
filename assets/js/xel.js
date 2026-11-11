// XLNF — xel.js
// Explicit analytics for /xel/ (Xel's room), in the notes.js convention.
//
//   xel_index_view    — /xel/ was opened                    { episodes: <count> }
//   xel_episode_view  — an episode page was opened          { slug, kind }
//   xel_outbound      — a tracked link was clicked           { to, placement, slug }
//       to:        github | guide | youtube | channel | episode | issue | docs | tool
//                  (the link's data-track; the last three are "Related reports and docs" links)
//       placement: episode (an episode page) | catalogue (/xel/)
//       slug:      the nearest [data-slug] — the <article> on an episode page, the
//                  entry <li> on the catalogue; null for the catalogue's channel button
//   xel_youtube_click — an explicit link to YouTube was clicked { destination, placement, episode_slug? }
//       destination: channel | short
//       placement:   room_button | episode_watch_link | episode_channel_link
//       episode_slug: episode pages only
//       Fired alongside xel_outbound (which stays the cross-destination event), by
//       the same listener. Sent at once by sendBeacon so it survives the navigation;
//       the link opens normally. Clicks inside the embedded player never reach this
//       page (cross-origin iframe), so they are not counted, and a click is not a view.

(function () {
  "use strict";

  function track(name, props, options) {
    if (window.xlnfTrack) window.xlnfTrack(name, props || {}, options);
  }

  // data-track value -> xel_youtube_click destination, for links that go to YouTube
  var YT_DESTINATION = { youtube: "short", channel: "channel" };
  var BEACON = { transport: "sendBeacon", send_instantly: true };

  function youtubeClick(a, to, placement, slug) {
    var host = (a.hostname || "").toLowerCase();
    if (!YT_DESTINATION[to] || !/(^|\.)youtube\.com$/.test(host)) return;
    var props = { destination: YT_DESTINATION[to] };
    if (placement === "episode") {
      props.placement = to === "youtube" ? "episode_watch_link" : "episode_channel_link";
      props.episode_slug = slug;
    } else {
      props.placement = "room_button";
    }
    track("xel_youtube_click", props, BEACON);
  }

  function init() {
    var article = document.querySelector("article[data-slug]");
    if (article) {
      track("xel_episode_view", { slug: article.getAttribute("data-slug"), kind: article.getAttribute("data-kind") });
    } else if (document.querySelector(".episodes, .empty")) {
      track("xel_index_view", { episodes: document.querySelectorAll(".episodes > li").length });
    }

    var placement = article ? "episode" : "catalogue";

    // One delegated listener: exactly one xel_outbound per click (plus one
    // xel_youtube_click for a YouTube link), whatever was clicked inside the link.
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[data-track]");
      if (!a) return;
      var owner = a.closest("[data-slug]");
      var to = a.getAttribute("data-track");
      var slug = owner ? owner.getAttribute("data-slug") : null;
      track("xel_outbound", { to: to, placement: placement, slug: slug });
      youtubeClick(a, to, placement, slug);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
