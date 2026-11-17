// XLNF — xel-search.js
// Filters the /xel/ catalogue as you type. Each entry carries data-search (title,
// summary, kind, series, transcript), written by xel-build.py. Every word typed
// must appear (AND), case- and accent-insensitive. The query is kept in ?q= so a
// filtered list can be shared or reloaded. "/" focuses the box, Esc clears it.
// No analytics: nothing typed here is sent anywhere.

(function () {
  "use strict";

  function norm(s) {
    return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"').toLowerCase();
  }

  function init() {
    var form = document.querySelector(".ep-search");
    var list = document.querySelector(".episodes");
    if (!form || !list) return;
    var input = form.querySelector("#ep-q");
    var count = form.querySelector("#ep-count");
    var none = document.getElementById("ep-none");
    var items = Array.prototype.map.call(list.children, function (li) {
      return { li: li, text: norm(li.getAttribute("data-search")) };
    });
    var total = items.length;

    function apply() {
      var terms = norm(input.value).split(/\s+/).filter(Boolean);
      var shown = 0;
      items.forEach(function (it) {
        var hit = terms.every(function (t) { return it.text.indexOf(t) !== -1; });
        it.li.hidden = !hit;
        if (hit) shown++;
      });
      count.textContent = terms.length ? shown + " of " + total + " episodes" : "";
      none.hidden = shown !== 0;
      try {
        var url = new URL(location.href);
        if (input.value.trim()) url.searchParams.set("q", input.value.trim());
        else url.searchParams.delete("q");
        history.replaceState(null, "", url);
      } catch (e) {}
    }

    function clear() { input.value = ""; apply(); input.focus(); }

    form.addEventListener("submit", function (e) { e.preventDefault(); });
    input.addEventListener("input", apply);
    input.addEventListener("keydown", function (e) { if (e.key === "Escape") clear(); });
    document.getElementById("ep-clear").addEventListener("click", clear);
    document.addEventListener("keydown", function (e) {
      var t = e.target;
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      if (t && (t.isContentEditable || /^(input|textarea|select)$/i.test(t.tagName))) return;
      e.preventDefault();
      input.focus();
    });

    try { input.value = new URLSearchParams(location.search).get("q") || ""; } catch (e) {}
    form.hidden = false;
    if (input.value) apply();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
