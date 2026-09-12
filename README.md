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

- `index.html` — the main human-facing card-site (header, decoder gag, intro, founder card, contact form, footer). All CSS is inlined in `<head>` for a single-request first paint. Includes JSON-LD structured data and `<link rel="alternate">` pointing at the LLM version.
- `llm.html` — structured profile for LLMs and AI agents. No JS, semantic HTML, entity metadata, operating model, stack choices.
- `llms.txt` — short markdown index following the [llmstxt.org](https://llmstxt.org) convention. Points agents at the core pages and gives the 3-sentence profile.
- `notes/` — the notes layer: technical write-ups, built for search discoverability. `notes/index.html` is the listing; each note is `notes/<slug>/index.html` so the URL is a clean `/notes/<slug>/` with no server config. See [Adding a note](#adding-a-note).
- `sitemap.xml` — hand-maintained; **every new page needs an entry**. There is no build step to generate it.
- `robots.txt` — present for intent, but see the caveat under [SEO](#seo).
- `check-notes.py` — dev-time consistency check for the notes layer; not served, not part of a build. Run it after adding a note.
- `assets/js/decoder.js` — XLNF backronym list + random pick + re-roll on click/Enter
- `assets/js/theme.js` — dark/light toggle with `localStorage` persistence
- `assets/js/contact.js` — AJAX submit of `#contact-form` to Formspree (endpoint `mrerljne`); includes honeypot
- `assets/js/scroll-top.js` — fixed "↑ top" button, appears after 400px scroll, smooth-scrolls to top
- `assets/js/analytics.js` — `window.xlnfTrack(name, props)` wrapper over PostHog. Init is inlined in `index.html` `<head>`. EU Cloud, cookieless (`persistence: "memory"`), autocapture off, session recording off. Tracked events: `decoder_reroll`, `theme_toggle`, `contact_submit` (+ automatic pageview).
- `assets/js/notes.js` — notes analytics: `note_view`, `note_read` (75% scroll depth) and `notes_index_view`. See [Analytics](#analytics).
- `assets/js/posthog.js` — the PostHog init, for pages that don't inline it. `index.html` keeps its own inlined copy so its pageview fires before first paint; notes load this deferred instead. **Two copies of the same config — change both.**
- `assets/css/notes.css` — shared stylesheet for `notes/`. The design tokens are duplicated from `index.html`'s inlined block, deliberately: inlining is what keeps the landing page a single request, and one shared file is what keeps N notes from drifting apart. Change tokens in both.
- `assets/fonts/` — JetBrains Mono (self-hosted)

## Adding a note

1. `mkdir notes/<slug>/` and write `index.html`. Copy the most recent note as the template — the head block carries a lot of required plumbing. Pick a slug that reads as a search query, not as a filename.
2. Update in the note's `<head>`: `<title>`, `meta description` (~155 chars), `link rel=canonical`, the `og:`/`twitter:` pairs, and both JSON-LD blocks (`TechArticle` + `BreadcrumbList`).
3. Add the note to **three** places or it stays invisible: `notes/index.html` (the list **and** the `blogPost` array in its JSON-LD), `sitemap.xml`, and `llms.txt`.
4. Optionally link it from the `notes` section of `index.html` — that list shows the three newest.
5. **Run `python3 check-notes.py`.** It fails if a note is missing from any of the three registries, if its canonical URL doesn't match its path, if a title or meta description is absent, or if any JSON-LD block won't parse. It also catches the reverse — a sitemap or `llms.txt` entry pointing at a note directory that no longer exists. Step 3 is easy to half-finish and the failure is silent, so don't skip this.
6. Preview locally, then check the rendered page with Google's Rich Results Test before announcing it anywhere.

Write original prose. Do not paste a project's README into a note: two copies of the same text on two domains compete with each other, and the note should be the *story* — what broke, what the wrong theories were, why the real cause is what it is — with the repo holding the instructions.

## Analytics

PostHog EU Cloud, cookieless, autocapture and session recording off. Pageviews are automatic (`capture_pageview: true`); everything else is an explicit `window.xlnfTrack(name, props)` call.

| Event | Fired when | Properties |
|---|---|---|
| `decoder_reroll` | the backronym is re-rolled | — |
| `theme_toggle` | theme switched | `to` |
| `contact_submit` | contact form submitted | — |
| `guild_revealed` / `guild_join` | hidden guild form revealed / submitted | — |
| `notes_index_view` | `/notes/` opened | `notes` (count) |
| `note_view` | a note page opened | `slug`, `title` |
| `note_read` | reader reached 75% of a note | `slug`, `title` |

`note_view` vs `note_read` is the distinction that matters: a pageview says a search result was clicked, not that anything was read. A note shorter than the viewport counts as read on load, which is correct rather than generous.

**Known limitation — `persistence: "memory"`.** Storage is session-scoped and nothing is written to the browser, which is what avoids needing a consent banner. PostHog itself warns about the cost at init:

> persistence is set to 'memory' but no bootstrap.distinctID was provided. PostHog will mint a new distinct ID on every page load.

So **a new distinct ID is minted per page load**. Consequences worth knowing before reading any dashboard: unique visitors is meaningless (it equals pageviews), and there is no session stitching — you cannot see one reader going note → note → homepage → contact. Per-note view and read counts are still accurate, which is what the notes layer is actually measured on.

Changing this means choosing persistent storage, which changes the site's privacy posture and likely requires a consent mechanism. It is a deliberate trade, not an oversight — don't "fix" it without deciding that question first.

## SEO

What is in place: per-page titles and descriptions, canonical URLs, Open Graph and Twitter cards, JSON-LD (`Organization` on the homepage, `Blog` on the notes index, `TechArticle` + breadcrumbs per note), a sitemap, and internal links in both directions between homepage, index and notes.

**The robots.txt caveat.** This is a *project* Pages site served from `/xlnf/`, so `robots.txt` only has authority at the domain root — `https://mihai-valentin.github.io/robots.txt` — which belongs to a `mihai-valentin.github.io` repo that does not currently exist. Crawlers will therefore never read `/xlnf/robots.txt`, and will never discover the `Sitemap:` line in it. Nothing is blocked (an absent robots.txt means crawl freely), but **the sitemap has to be submitted by hand** in Google Search Console and Bing Webmaster Tools. The file is kept as a statement of intent and so it is already correct if a user-level Pages repo ever appears.

Canonical URLs are absolute and hardcoded to `mihai-valentin.github.io/xlnf`. Moving to a custom domain means updating them in every page, plus `sitemap.xml`.

## License

© XLNF. All rights reversed.
