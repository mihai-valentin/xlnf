// XLNF — notes.js
// Explicit analytics for the notes layer.
//
// PostHog's automatic $pageview already records that a note was loaded, but it
// is only distinguishable by URL. These events follow the site's existing
// manual-event convention (decoder_reroll, theme_toggle, contact_submit) and
// carry the slug as a property, so notes can be compared without parsing URLs.
//
//   note_view  — an article page was opened       { slug, title }
//   note_read  — the reader reached 75% of it     { slug, title }
//   notes_index_view — the listing was opened     { notes: <count> }
//
// note_read is the one that matters: a pageview says a search result was
// clicked, not that anything was read.

(function () {
  "use strict";

  var READ_FRACTION = 0.75;

  function track(name, props) {
    if (window.xlnfTrack) window.xlnfTrack(name, props || {});
  }

  function slugFromPath() {
    // /notes/<slug>/ -> <slug>   (trailing "index.html" tolerated)
    var parts = window.location.pathname.split("/").filter(function (p) {
      return p && p !== "index.html";
    });
    var i = parts.lastIndexOf("notes");
    if (i === -1) return null;
    return parts.length > i + 1 ? parts[i + 1] : null;
  }

  function init() {
    var article = document.querySelector("article");
    var slug = slugFromPath();

    if (!article || !slug) {
      // the listing page, not a note
      if (document.querySelector(".note-list")) {
        track("notes_index_view", {
          notes: document.querySelectorAll(".note-list > li").length,
        });
      }
      return;
    }

    var h1 = document.querySelector("h1");
    var meta = { slug: slug, title: h1 ? h1.textContent.trim() : document.title };

    track("note_view", meta);

    var fired = false;
    function check() {
      if (fired) return;
      var doc = document.documentElement;
      var scrollable = doc.scrollHeight - window.innerHeight;
      // A page shorter than the viewport is fully visible, so it counts as read.
      var progress = scrollable > 0 ? window.scrollY / scrollable : 1;
      if (progress >= READ_FRACTION) {
        fired = true;
        window.removeEventListener("scroll", check);
        track("note_read", meta);
      }
    }

    window.addEventListener("scroll", check, { passive: true });
    check();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
