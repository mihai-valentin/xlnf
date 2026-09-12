# XLNF — legacy location

**The site has moved to [xlnf.dev](https://xlnf.dev/). This branch is not the live site.**

`master` exists only to keep old GitHub Pages URLs working while search engines
and existing links migrate. It serves one canonical pointer per page:

| Old URL | Canonical URL |
|---|---|
| `mihai-valentin.github.io/xlnf/` | `https://xlnf.dev/` |
| `mihai-valentin.github.io/xlnf/notes/` | `https://xlnf.dev/notes/` |
| `mihai-valentin.github.io/xlnf/notes/<slug>/` | `https://xlnf.dev/notes/<slug>/` |
| `mihai-valentin.github.io/xlnf/llm.html` | `https://xlnf.dev/llm.html` |

Each page carries a `rel=canonical` at its xlnf.dev equivalent plus a 0-second
`meta refresh`. GitHub Pages cannot issue real HTTP 301s for arbitrary paths —
there is no server config to put them in — so that pair is the closest honest
static equivalent: the canonical transfers ranking signals, the refresh moves
people.

`noindex` is deliberately absent. Alongside a canonical it contradicts itself —
`noindex` asks for the URL to be dropped while the canonical asks for its signals
to be transferred, and dropping it without transferring anything is the worst of
the three outcomes. `robots.txt` also still allows crawling, because a blocked
crawler never reads the canonical tags that make the move consolidate.

## Source of truth

- **Live site and all development:** the [`main`](../../tree/main) branch, deployed to
  [xlnf.dev](https://xlnf.dev/) via DigitalOcean App Platform on every push.
- **This branch:** frozen. Do not add content or develop here.

Once the migration has settled, GitHub Pages can be switched off and this branch
deleted.
