// XLNF — contact.js
// POSTs #contact-form to Formspree via fetch; renders inline status.

(function () {
  "use strict";

  const ENDPOINT = "https://formspree.io/f/mrerljne";

  function setStatus(el, text, state) {
    el.textContent = text;
    el.dataset.state = state || "";
  }

  function init() {
    const form = document.getElementById("contact-form");
    if (!form) return;
    const status = document.getElementById("contact-status");
    const submit = document.getElementById("contact-submit");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      // Honeypot: bots fill hidden fields; real users don't.
      if (form.querySelector('[name="_gotcha"]').value) return;
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
          setStatus(status, "sent. we'll be in touch.", "success");
          if (window.xlnfTrack) window.xlnfTrack("contact_submit", { ok: true });
        } else {
          const data = await res.json().catch(() => ({}));
          const msg =
            (data.errors && data.errors.map((x) => x.message).join("; ")) ||
            "submission failed";
          setStatus(status, msg, "error");
          if (window.xlnfTrack) window.xlnfTrack("contact_submit", { ok: false, status: res.status });
        }
      } catch (_err) {
        setStatus(status, "network error — try again later", "error");
        if (window.xlnfTrack) window.xlnfTrack("contact_submit", { ok: false, network_error: true });
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
