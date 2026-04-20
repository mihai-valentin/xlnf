# XLNF

> Xtremely Lightweight Nonsense Factory · eXperimental Lab for Nebulous Futures · eXecutable Late-Night Fever-dreams

The public site for XLNF — a consultancy, a lab, and a vibe. Single-page **card-site**. Plain HTML/CSS/JS, zero build step, served via GitHub Pages.

## Local preview

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy

Push to `main`. GitHub Pages serves from the repo root. `.nojekyll` disables Jekyll so `assets/` paths work as-is.

## Structure

- `index.html` — the one and only page (header, decoder gag, intro, founder card, contact form, footer). All CSS is inlined in `<head>` for a single-request first paint.
- `assets/js/decoder.js` — XLNF backronym list + random pick + re-roll on click/Enter
- `assets/js/theme.js` — dark/light toggle with `localStorage` persistence
- `assets/js/contact.js` — AJAX submit of `#contact-form` to Formspree (endpoint `mrerljne`); includes honeypot
- `assets/js/guild.js` — hidden dev-guild signup. Section `#guild` revealed when URL hash is `#guild`; AJAX submit to Formspree (endpoint `xkokzezl`)
- `assets/js/scroll-top.js` — fixed "↑ top" button, appears after 400px scroll, smooth-scrolls to top
- `assets/js/analytics.js` — `window.xlnfTrack(name, props)` wrapper over PostHog. Init is inlined in `index.html` `<head>`. EU Cloud, cookieless (`persistence: "memory"`), autocapture off, session recording off. Tracked events: `decoder_reroll`, `theme_toggle`, `contact_submit` (+ automatic pageview).
- `assets/fonts/` — JetBrains Mono (self-hosted)

## License

© XLNF. All rights reversed.
