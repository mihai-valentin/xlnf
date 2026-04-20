// XLNF — guild.js
// Secondary form module. Section #guild is revealed when location.hash === "#guild".

(function () {
  "use strict";

  const ENDPOINT = "https://formspree.io/f/xkokzezl";

  function setStatus(el, text, state) {
    el.textContent = text;
    el.dataset.state = state || "";
  }

  function reveal() {
    const sec = document.getElementById("guild");
    if (!sec || !sec.hidden) return;
    sec.hidden = false;
    sec.setAttribute("aria-hidden", "false");
    sec.scrollIntoView({ behavior: "smooth", block: "start" });
    const emailInput = document.querySelector("#guild-form [name=email]");
    if (emailInput) emailInput.focus({ preventScroll: true });
    if (window.xlnfTrack) window.xlnfTrack("guild_revealed");
  }

  function init() {
    if (location.hash === "#guild") reveal();
    window.addEventListener("hashchange", () => {
      if (location.hash === "#guild") reveal();
    });

    const form = document.getElementById("guild-form");
    if (!form) return;
    const status = document.getElementById("guild-status");
    const submit = document.getElementById("guild-submit");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (form.querySelector('[name="_gotcha"]').value) return; // honeypot tripped
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      submit.disabled = true;
      setStatus(status, "sending...", "pending");
      try {
        const res = await fetch(ENDPOINT, {
          method: "POST",
          headers: { Accept: "application/json" },
          body: new FormData(form),
        });
        if (res.ok) {
          form.reset();
          setStatus(status, "enlisted. welcome to the guild.", "success");
          if (window.xlnfTrack) window.xlnfTrack("guild_join", { ok: true });
        } else {
          const data = await res.json().catch(() => ({}));
          const msg =
            (data.errors && data.errors.map((x) => x.message).join("; ")) ||
            "submission failed";
          setStatus(status, msg, "error");
          if (window.xlnfTrack) window.xlnfTrack("guild_join", { ok: false, status: res.status });
        }
      } catch (_err) {
        setStatus(status, "network error — try again later", "error");
        if (window.xlnfTrack) window.xlnfTrack("guild_join", { ok: false, network_error: true });
      } finally {
        submit.disabled = false;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
