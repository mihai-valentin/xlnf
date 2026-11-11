#!/usr/bin/env python3
"""Render the /xel/ section from episode data, and register it everywhere.

The site has no build step for visitors; this is a dev-time generator, like
check-notes.py is a dev-time check. Its output is committed and served as-is.

Input (the contract with agent-research-blogger's `arb page`):
    xel/<slug>/episode.json   episode data — schema in README.md → "Xel episodes"
    xel/<slug>/poster.jpg     9:16 poster (filename set by episode.json "poster")

Output (all generated; never hand-edit):
    xel/<slug>/index.html     from templates/xel-episode.html
    xel/index.html            from templates/xel-index.html, episodes newest first
    sitemap.xml               region between <!-- xel:start --> / <!-- xel:end -->
    llm.html                  list region + ItemList JSON-LD region (xel:* markers)
    llms.txt                  the "## Xel" section, up to the next "## " heading

index.html links to /xel/ with a static, hand-written link; it is not touched.

Usage:
    python3 xel-build.py           # write everything
    python3 xel-build.py --check   # write nothing; exit 1 if anything is stale
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://xlnf.dev"

# Xel's YouTube channel. Change it here, then rebuild.
CHANNEL_URL = "https://www.youtube.com/@xelxlnf"

KINDS = ("teaser", "digest", "explainer", "deep-dive")
# Teasers carry no facts, so they render no Sources section and no claim chips.
# Every other kind must cite at least one sourced claim.
SOURCELESS_KINDS = ("teaser",)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
CLAIM_ID_RE = re.compile(r"^[A-Z]+[0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLOT_RE = re.compile(r"\{\{([a-z_]+)\}\}")
ACTION_KIND_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REFERENCE_KINDS = ("issue", "docs", "tool")
# Short labels for an episode's actions on the /xel/ catalogue entry (the episode
# page shows the full `label` from episode.json). Unknown kinds fall back to `label`.
CATALOGUE_LABELS = {"fix": "Get the fix", "guide": "Read the explanation"}


class EpisodeError(Exception):
    pass


def esc(s):
    return html.escape(s or "", quote=True)


def path(*p):
    return os.path.join(ROOT, *p)


def read(p):
    with open(path(p), encoding="utf-8") as f:
        return f.read()


# ----------------------------------------------------------------- loading

def load_episode(slug):
    rel = f"xel/{slug}/episode.json"
    try:
        ep = json.loads(read(rel))
    except json.JSONDecodeError as e:
        raise EpisodeError(f"{rel}: not valid JSON ({e})")

    def need(key, kind=str):
        v = ep.get(key)
        if not isinstance(v, kind) or (kind is str and not v.strip()):
            raise EpisodeError(f"{rel}: '{key}' is required ({kind.__name__})")
        return v

    if ep.get("schema") != 1:
        raise EpisodeError(f"{rel}: 'schema' must be 1")
    if need("slug") != slug:
        raise EpisodeError(f"{rel}: slug '{ep['slug']}' does not match its directory '{slug}'")
    need("title")
    if not DATE_RE.match(need("date")):
        raise EpisodeError(f"{rel}: 'date' must be YYYY-MM-DD")
    if ep.get("updated") is not None and not DATE_RE.match(str(ep["updated"])):
        raise EpisodeError(f"{rel}: 'updated' must be YYYY-MM-DD or absent")
    if need("kind") not in KINDS:
        raise EpisodeError(f"{rel}: 'kind' must be one of {', '.join(KINDS)}")
    summary = need("summary")
    if len(summary) > 200:
        raise EpisodeError(f"{rel}: 'summary' is {len(summary)} chars; it doubles as the meta description, keep it ≤ 200")
    yt = ep.get("youtube_id")
    if yt is not None and not (isinstance(yt, str) and YT_ID_RE.match(yt)):
        raise EpisodeError(f"{rel}: 'youtube_id' must be an 11-char YouTube video ID or null")
    dur = ep.get("duration_seconds")
    if dur is not None and not isinstance(dur, (int, float)):
        raise EpisodeError(f"{rel}: 'duration_seconds' must be a number or null")
    poster = need("poster")
    if "/" in poster or not os.path.isfile(path("xel", slug, poster)):
        raise EpisodeError(f"{rel}: poster '{poster}' must be a file inside xel/{slug}/")
    need("disclosure")
    if not isinstance(ep.get("body_html", ""), str):
        raise EpisodeError(f"{rel}: 'body_html' must be a string (may be empty)")

    actions = ep.get("actions")
    if actions is not None:
        if not isinstance(actions, list) or not actions:
            raise EpisodeError(f"{rel}: 'actions' must be a non-empty list or absent")
        for i, a in enumerate(actions):
            where = f"{rel}: actions[{i}]"
            if not isinstance(a, dict):
                raise EpisodeError(f"{where}: must be an object")
            if not ACTION_KIND_RE.match(str(a.get("kind", ""))):
                raise EpisodeError(f"{where}: 'kind' is required ([a-z0-9-], e.g. fix, guide)")
            if not (isinstance(a.get("label"), str) and a["label"].strip()):
                raise EpisodeError(f"{where}: 'label' is required")
            if not re.match(r"^https://", str(a.get("url", ""))):
                raise EpisodeError(f"{where}: 'url' must be https")
            if not isinstance(a.get("primary", False), bool):
                raise EpisodeError(f"{where}: 'primary' must be true, false or absent")
        if sum(1 for a in actions if a.get("primary")) > 1:
            raise EpisodeError(f"{rel}: at most one action may be primary")
    applies_to = ep.get("applies_to")
    if applies_to is not None and not (isinstance(applies_to, str) and applies_to.strip()):
        raise EpisodeError(f"{rel}: 'applies_to' must be a non-empty string or absent")
    for key in ("requirements", "limitations"):
        v = ep.get(key)
        if v is not None and not (isinstance(v, list) and v and all(isinstance(x, str) and x.strip() for x in v)):
            raise EpisodeError(f"{rel}: '{key}' must be a non-empty list of strings or absent")

    refs = ep.get("references")
    if refs is not None:
        if not isinstance(refs, list) or not refs:
            raise EpisodeError(f"{rel}: 'references' must be a non-empty list or absent")
        seen = set()
        for i, r in enumerate(refs):
            where = f"{rel}: references[{i}]"
            if not isinstance(r, dict):
                raise EpisodeError(f"{where}: must be an object")
            if not (isinstance(r.get("label"), str) and r["label"].strip()):
                raise EpisodeError(f"{where}: 'label' is required")
            if not re.match(r"^https://", str(r.get("url", ""))):
                raise EpisodeError(f"{where}: 'url' must be https")
            if r["url"] in seen:
                raise EpisodeError(f"{where}: duplicate url {r['url']}")
            seen.add(r["url"])
            if r.get("kind") not in REFERENCE_KINDS:
                raise EpisodeError(f"{where}: 'kind' must be one of {', '.join(REFERENCE_KINDS)}")
            if r.get("note") is not None and not (isinstance(r["note"], str) and r["note"].strip()):
                raise EpisodeError(f"{where}: 'note' must be a non-empty string or absent")
    rf = ep.get("references_from")
    if rf is not None and not (refs and re.match(r"^https://", str(rf))):
        raise EpisodeError(f"{rel}: 'references_from' must be an https url, and needs 'references'")

    claims = ep.get("claims") or []
    sourced = ep["kind"] not in SOURCELESS_KINDS
    if sourced and not claims:
        raise EpisodeError(f"{rel}: kind '{ep['kind']}' needs at least one claim in 'claims'")
    ids = set()
    for i, c in enumerate(claims):
        where = f"{rel}: claims[{i}]"
        cid = c.get("id", "")
        if not CLAIM_ID_RE.match(cid):
            raise EpisodeError(f"{where}: 'id' must look like C001")
        if cid in ids:
            raise EpisodeError(f"{where}: duplicate id {cid}")
        ids.add(cid)
        if not (c.get("statement") or "").strip():
            raise EpisodeError(f"{where}: 'statement' is required")
        quotes = c.get("quotes")
        if not quotes or not all(isinstance(q, str) and q.strip() for q in quotes):
            raise EpisodeError(f"{where}: 'quotes' needs at least one verbatim quote")
        src = c.get("source") or {}
        has_repo = src.get("project") and src.get("path") and src.get("commit")
        if not (has_repo or src.get("url")):
            raise EpisodeError(f"{where}: 'source' needs project+path+commit, or a url")
        if src.get("commit") and not re.match(r"^[0-9a-f]{7,40}$", src["commit"]):
            raise EpisodeError(f"{where}: source.commit must be a hex commit hash")
        if src.get("url") and not re.match(r"^https?://", src["url"]):
            raise EpisodeError(f"{where}: source.url must be http(s)")

    for i, line in enumerate(ep.get("transcript") or []):
        if not (line.get("text") or "").strip():
            raise EpisodeError(f"{rel}: transcript[{i}] has no text")
        for ref in line.get("claims") or []:
            if ref not in ids:
                raise EpisodeError(f"{rel}: transcript[{i}] cites {ref}, which is not in claims")
    transcript = ep.get("transcript") or []
    if sourced and transcript and not any(line.get("claims") for line in transcript):
        raise EpisodeError(f"{rel}: kind '{ep['kind']}' has a transcript but no line cites a claim")
    return ep


def load_all():
    slugs = sorted(
        os.path.basename(os.path.dirname(p))
        for p in glob.glob(path("xel", "*", "episode.json"))
    )
    eps, errors = [], []
    for slug in slugs:
        if not SLUG_RE.match(slug):
            errors.append(f"xel/{slug}/: directory name is not a valid slug")
            continue
        try:
            eps.append(load_episode(slug))
        except EpisodeError as e:
            errors.append(str(e))
    # newest first; same-day ties broken by slug for a stable order
    eps.sort(key=lambda e: e["slug"])
    eps.sort(key=lambda e: e["date"], reverse=True)
    return eps, errors


# ----------------------------------------------------------------- helpers

def fill(template, slots, name):
    template = re.sub(r"\A(<!doctype html>\n)<!--.*?-->\n", r"\1", template, count=1, flags=re.S)
    def sub(m):
        key = m.group(1)
        if key not in slots:
            raise KeyError(f"{name}: no value for slot {{{{{key}}}}}")
        return slots[key]
    out = SLOT_RE.sub(sub, template)
    notice = f"<!-- GENERATED by xel-build.py from templates/{name} — do not edit by hand. -->\n"
    return out.replace("<!doctype html>\n", "<!doctype html>\n" + notice, 1)


def jsonld(obj):
    return "\n".join("  " + line for line in json.dumps(obj, indent=2, ensure_ascii=False).split("\n"))


def url_for(ep):
    return f"{BASE}/xel/{ep['slug']}/"


def fmt_duration(sec):
    return f"{sec:g} s"


def action_href(url):
    """Same-site links stay relative-to-root so they also work in a local preview."""
    return url[len(BASE):] if url.startswith(BASE + "/") else url


def action_track(a):
    """xel_outbound `to` value: where the link goes, not what it is called."""
    host = re.sub(r"^https://([^/]+).*$", r"\1", a["url"]).lower()
    if host in ("github.com", "www.github.com"):
        return "github"
    return a["kind"]


def action_link(a, label, cls="btn", primary_cls="btn primary"):
    href = action_href(a["url"])
    rel = "" if href.startswith("/") else ' rel="noopener"'
    return (f'<a class="{primary_cls if a.get("primary") else cls}" href="{esc(href)}"'
            f' data-track="{esc(action_track(a))}"{rel}>{esc(label)}</a>')


def short_commit(c):
    return c[:7]


def source_html(src):
    parts = []
    if src.get("project"):
        loc = src.get("path", "")
        if src.get("lines"):
            loc += f":{src['lines']}"
        label = f"<strong>{esc(src['project'])}</strong> · <code>{esc(loc)}</code>"
        if src.get("commit"):
            label += f' @ <code title="{esc(src["commit"])}">{esc(short_commit(src["commit"]))}</code>'
        parts.append(label)
    if src.get("url"):
        shown = esc(src["url"]) if not src.get("project") else "source"
        parts.append(f'<a href="{esc(src["url"])}" rel="noopener">{shown}</a>')
    elif src.get("project"):
        parts.append("private repository, no public link")
    return " · ".join(parts)


# ----------------------------------------------------------------- episode page

def render_episode(ep, template):
    slug, yt = ep["slug"], ep.get("youtube_id")
    canonical = url_for(ep)
    poster_abs = f"{BASE}/xel/{slug}/{ep['poster']}"
    title = ep["title"]
    I = " " * 14  # indentation inside <figure>

    if yt:
        video = (
            f'{I}<div class="frame916">\n'
            f'{I}  <iframe src="https://www.youtube-nocookie.com/embed/{yt}" title="{esc(title)} — YouTube Short"'
            f' loading="lazy" referrerpolicy="strict-origin-when-cross-origin"'
            f' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"'
            f' allowfullscreen></iframe>\n'
            f'{I}</div>'
        )
    else:
        video = (
            f'{I}<div class="frame916" data-video="pending">\n'
            f'{I}  <img src="{esc(ep["poster"])}" width="720" height="1280" alt="Poster for the Short: {esc(title)}">\n'
            f'{I}  <span class="soon">Short coming soon</span>\n'
            f'{I}</div>'
        )

    watch = (
        f'<a class="btn primary" href="https://www.youtube.com/shorts/{yt}" data-track="youtube" rel="noopener">▶ Watch on YouTube</a>'
        if yt else '<span class="btn pending" aria-disabled="true">▶ On YouTube soon</span>'
    )
    channel = (
        f'<a class="btn" href="{esc(CHANNEL_URL)}" data-track="channel" rel="noopener">Xel on YouTube</a>'
        if CHANNEL_URL else '<!-- TODO(channel-url) --><span class="btn pending" aria-disabled="true">Channel link soon</span>'
    )
    J = " " * 14
    # The watch button lives only under the Short; the end-of-page links don't repeat it.
    links = "\n".join(J + x for x in (channel, '<a class="btn" href="../">← Xel\'s room</a>'))
    video += f'\n{I}<div class="actions">\n{I}  {watch}\n{I}</div>'

    S = " " * 12
    transcript_section = ""
    sourced = ep["kind"] not in SOURCELESS_KINDS
    if ep.get("transcript"):
        items = []
        for line in ep["transcript"]:
            cites = "".join(
                f'<a href="#{esc(c.lower())}">{esc(c)}</a>' for c in (line.get("claims") or [] if sourced else [])
            )
            cite_html = f' <span class="cite">{cites}</span>' if cites else ""
            items.append(f"{S}  <li>{esc(line['text'])}{cite_html}</li>")
        transcript_section = (
            f'{S}<section aria-labelledby="said">\n'
            f'{S}<h2 id="said">What I said</h2>\n'
            f'{S}<ol class="transcript">\n' + "\n".join(items) + f"\n{S}</ol>\n{S}</section>"
        )

    body_section = ""
    if (ep.get("body_html") or "").strip():
        body_section = (
            f'{S}<section aria-labelledby="writeup">\n{S}<h2 id="writeup">Write-up</h2>\n'
            f'{S}<div class="body">\n{ep["body_html"].strip()}\n{S}</div>\n{S}</section>'
        )

    claims_section = ""
    if sourced and ep.get("claims"):
        cards = []
        for c in ep["claims"]:
            quotes = "\n".join(f"{S}    <blockquote>{esc(q)}</blockquote>" for q in c["quotes"])
            cards.append(
                f'{S}  <li class="claim card" id="{esc(c["id"].lower())}">\n'
                f'{S}    <span class="claim-id">{esc(c["id"])}</span>\n'
                f'{S}    <p class="statement">{esc(c["statement"])}</p>\n'
                f"{quotes}\n"
                f'{S}    <p class="source">{source_html(c["source"])}</p>\n'
                f"{S}  </li>"
            )
        claims_section = (
            f'{S}<section aria-labelledby="sources">\n{S}<h2 id="sources">Sources</h2>\n'
            f'{S}<p class="meta">Each claim, with the evidence quoted verbatim from the source it traces to.</p>\n'
            f'{S}<ol class="claims">\n' + "\n".join(cards) + f"\n{S}</ol>\n{S}</section>"
        )

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": ep["summary"],
        "datePublished": ep["date"],
        "dateModified": ep.get("updated") or ep["date"],
        "inLanguage": "en",
        "url": canonical,
        "mainEntityOfPage": canonical,
        "image": poster_abs,
        "genre": ep["kind"],
        "author": {"@type": "Organization", "name": "XLNF", "url": f"{BASE}/"},
        "publisher": {"@type": "Organization", "name": "XLNF", "url": f"{BASE}/"},
        "isPartOf": {"@type": "CollectionPage", "name": "Xel's room", "url": f"{BASE}/xel/"},
    }
    if yt:
        video_obj = {
            "@type": "VideoObject",
            "name": title,
            "description": ep["summary"],
            "thumbnailUrl": poster_abs,
            "uploadDate": ep["date"],
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{yt}",
            "contentUrl": f"https://www.youtube.com/shorts/{yt}",
        }
        if ep.get("duration_seconds"):
            video_obj["duration"] = f"PT{ep['duration_seconds']:g}S"
        article["video"] = video_obj
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "XLNF", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Xel's room", "item": f"{BASE}/xel/"},
            {"@type": "ListItem", "position": 3, "name": title},
        ],
    }

    H = " " * 10  # indentation inside <header class="ep-head">
    if ep.get("actions"):
        # Problem-first layout: title, who it applies to, then the actions;
        # the summary moves below the Short, at the top of the main column.
        lead = ""
        if ep.get("applies_to"):
            lead += f'\n{H}<p class="applies"><span class="label">Applies to</span> {esc(ep["applies_to"])}</p>'
        ordered = sorted(ep["actions"], key=lambda a: not a.get("primary"))
        lead += (f'\n{H}<nav class="actions ep-actions" aria-label="what to do next">\n'
                 + "\n".join(f"{H}  {action_link(a, a['label'])}" for a in ordered)
                 + f"\n{H}</nav>")
        main_summary = f'{S}<p class="summary">{esc(ep["summary"])}</p>\n'
    else:
        lead = f'\n{H}<p class="summary">{esc(ep["summary"])}</p>'
        main_summary = ""

    fit_section = ""
    blocks = [(k, h) for k, h in (("requirements", "What you need"), ("limitations", "Limitations")) if ep.get(k)]
    if blocks:
        parts = []
        for key, heading in blocks:
            items = "\n".join(f"{S}  <li>{esc(x)}</li>" for x in ep[key])
            parts.append(f'{S}<section aria-labelledby="{key}">\n{S}<h2 id="{key}">{heading}</h2>\n'
                         f'{S}<ul class="facts">\n{items}\n{S}</ul>\n{S}</section>')
        fit_section = "\n".join(parts) + "\n"

    # Further reading, not evidence: it never goes in Sources and makes no claim.
    if ep.get("references"):
        items = []
        for r in ep["references"]:
            note = f' — {esc(r["note"])}' if r.get("note") else ""
            items.append(f'{S}  <li><a href="{esc(r["url"])}" data-track="{esc(r["kind"])}" rel="noopener">{esc(r["label"])}</a>{note}</li>')
        origin = ""
        if ep.get("references_from"):
            m = re.match(r"^https://github\.com/[^/]+/([^/#]+)", ep["references_from"])
            name = f"the {esc(m.group(1))} README" if m else "the source list"
            origin = f'{S}<p class="meta">Listed in <a href="{esc(ep["references_from"])}" data-track="github" rel="noopener">{name}</a>.</p>\n'
        fit_section += (f'{S}<section aria-labelledby="references">\n{S}<h2 id="references">Related reports and docs</h2>\n'
                        f'{origin}{S}<ul class="refs">\n' + "\n".join(items) + f"\n{S}</ul>\n{S}</section>\n")

    dur = ep.get("duration_seconds")
    slots = {
        "title": esc(title),
        "description": esc(ep["summary"]),
        "canonical": canonical,
        "poster_abs": poster_abs,
        "date": ep["date"],
        "kind": ep["kind"],
        "slug": slug,
        "lead": lead,
        "main_top": main_summary + fit_section,
        "duration_meta": f" · {fmt_duration(dur)}" if dur else "",
        "jsonld_article": jsonld(article),
        "jsonld_breadcrumb": jsonld(breadcrumb),
        "video": video,
        "transcript_section": transcript_section,
        "body_section": body_section,
        "claims_section": claims_section,
        "disclosure": esc(ep["disclosure"]),
        "links": links,
    }
    out = fill(template, slots, "xel-episode.html")
    return re.sub(r"\n{3,}", "\n\n", out)


# ----------------------------------------------------------------- landing page

def render_index(eps, template):
    I = " " * 6
    if eps:
        cards = []
        for ep in eps:
            dur = ep.get("duration_seconds")
            extra = ""
            if ep.get("actions"):
                links = [action_link(a, CATALOGUE_LABELS.get(a["kind"], a["label"])) for a in
                         sorted(ep["actions"], key=lambda a: not a.get("primary"))]
                links.append(f'<a class="btn" href="{ep["slug"]}/" data-track="episode">Watch the episode</a>')
                # links straight after the title: on a phone they must show on first load
                extra = (f'{I}      <p class="actions entry-actions">\n'
                         + "\n".join(f"{I}        {x}" for x in links) + f"\n{I}      </p>\n")
            cards.append(
                f'{I}  <li class="episode-card" data-slug="{ep["slug"]}">\n'
                f'{I}    <a href="{ep["slug"]}/" tabindex="-1" aria-hidden="true"><img class="thumb" src="{ep["slug"]}/{esc(ep["poster"])}" width="120" height="213" alt="" loading="lazy"></a>\n'
                f"{I}    <div>\n"
                f'{I}      <p class="kicker"><span class="kind">{ep["kind"]}</span> <span class="meta"><time datetime="{ep["date"]}">{ep["date"]}</time>{" · " + fmt_duration(dur) if dur else ""}</span></p>\n'
                f'{I}      <h3><a href="{ep["slug"]}/">{esc(ep["title"])}</a></h3>\n'
                f'{extra}{I}      <p>{esc(ep["summary"])}</p>\n'
                f"{I}    </div>\n"
                f"{I}  </li>"
            )
        episodes = f'{I}<ol class="episodes">\n' + "\n".join(cards) + f"\n{I}</ol>"
    else:
        episodes = f'{I}<p class="empty">No episodes yet.</p>'

    channel_button = (
        f'          <a class="btn primary" href="{esc(CHANNEL_URL)}" data-track="channel" rel="noopener">▶ Xel on YouTube</a>'
        if CHANNEL_URL
        else '          <!-- TODO(channel-url) --><span class="btn pending" aria-disabled="true">▶ YouTube channel soon</span>'
    )
    collection = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Xel's room",
        "description": "Pages for the YouTube Shorts by Xel, XLNF's AI research agent.",
        "url": f"{BASE}/xel/",
        "publisher": {"@type": "Organization", "name": "XLNF", "url": f"{BASE}/"},
        "hasPart": [
            {"@type": "Article", "headline": ep["title"], "url": url_for(ep), "datePublished": ep["date"]}
            for ep in eps
        ],
    }
    if CHANNEL_URL:
        collection["sameAs"] = CHANNEL_URL
    return fill(template, {
        "episodes": episodes,
        "channel_button": channel_button,
        "jsonld_collection": jsonld(collection),
    }, "xel-index.html")


# ----------------------------------------------------------------- registries

def replace_region(text, start, end, body, fname):
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pat.search(text):
        raise SystemExit(f"{fname}: markers {start} … {end} not found")
    return pat.sub(lambda _: start + body + end, text, count=1)


def render_sitemap(eps, text):
    newest = max((e.get("updated") or e["date"] for e in eps), default=None)
    entries = []
    if newest:
        entries.append((f"{BASE}/xel/", newest, None, "0.7"))
    for ep in eps:
        entries.append((url_for(ep), ep.get("updated") or ep["date"], None, "0.6"))
    body = "\n" + "".join(
        f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{mod}</lastmod>\n"
        # no <changefreq>: Xel promises no publishing cadence, not even to crawlers
        f"    <priority>{prio}</priority>\n  </url>\n"
        for loc, mod, freq, prio in entries
    ) + "  "
    return replace_region(text, "<!-- xel:start -->", "<!-- xel:end -->", body, "sitemap.xml")


def render_llm_html(eps, text):
    items = "".join(
        f'  <li>\n    <a href="xel/{ep["slug"]}/">{esc(ep["title"])}</a> · {ep["date"]} · {ep["kind"]}<br>\n'
        f'    <span class="meta">{esc(ep["summary"])}</span>\n  </li>\n'
        for ep in eps
    )
    body = "\n<ul>\n" + items + "</ul>\n" if eps else "\n<p>No episodes yet.</p>\n"
    text = replace_region(text, "<!-- xel:list:start -->", "<!-- xel:list:end -->", body, "llm.html")
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Xel's room — episodes",
        "description": "Episodes in Xel's room (https://xlnf.dev/xel/), Xel's section of xlnf.dev, with pages for the YouTube Shorts by Xel, XLNF's AI research agent: the video and its transcript.",
        "url": f"{BASE}/xel/",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(eps),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": url_for(ep), "name": ep["title"]}
            for i, ep in enumerate(eps)
        ],
    }
    block = '\n  <script type="application/ld+json">\n' + jsonld(itemlist) + "\n  </script>\n  "
    return replace_region(text, "<!-- xel:jsonld:start -->", "<!-- xel:jsonld:end -->", block, "llm.html")


def render_llms_txt(eps, text):
    lines = [
        "## Xel",
        "",
        "Xel is an AI research agent from XLNF that presents YouTube Shorts about software projects and the AI-agent world.",
        "",
        f"Xel's room ({BASE}/xel/): Xel's section of xlnf.dev, with pages for its Shorts: the video and its transcript.",
        "",
    ]
    if CHANNEL_URL:
        lines.append(f"- [Xel on YouTube]({CHANNEL_URL}): the channel.")
    for ep in eps:
        lines.append(f"- [{ep['title']}](xel/{ep['slug']}/) ({ep['date']}, {ep['kind']}): {ep['summary']}")
    section = "\n".join(lines) + "\n\n"
    m = re.search(r"^## Xel\n.*?(?=^## )", text, re.S | re.M)
    if m:
        return text[: m.start()] + section + text[m.end():]
    anchor = re.search(r"^## Entity\n", text, re.M)
    if not anchor:
        raise SystemExit("llms.txt: neither a '## Xel' section nor a '## Entity' heading to insert before")
    return text[: anchor.start()] + section + text[anchor.start():]


# ----------------------------------------------------------------- main

def plan():
    eps, errors = load_all()
    if errors:
        return None, errors
    ep_tpl = read("templates/xel-episode.html")
    out = {f"xel/{ep['slug']}/index.html": render_episode(ep, ep_tpl) for ep in eps}
    out["xel/index.html"] = render_index(eps, read("templates/xel-index.html"))
    out["sitemap.xml"] = render_sitemap(eps, read("sitemap.xml"))
    out["llm.html"] = render_llm_html(eps, read("llm.html"))
    out["llms.txt"] = render_llms_txt(eps, read("llms.txt"))
    return out, []


def main():
    check = "--check" in sys.argv[1:]
    out, errors = plan()
    if errors:
        print("FAIL — episode data is invalid:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    stale = []
    for rel, content in out.items():
        current = read(rel) if os.path.exists(path(rel)) else None
        if current == content:
            continue
        stale.append(rel)
        if not check:
            os.makedirs(os.path.dirname(path(rel)) or ROOT, exist_ok=True)
            with open(path(rel), "w", encoding="utf-8") as f:
                f.write(content)

    n = sum(1 for k in out if k.startswith("xel/") and k != "xel/index.html")
    if check:
        if stale:
            print("FAIL — generated files are stale; run python3 xel-build.py:")
            for rel in stale:
                print(f"  - {rel}")
            sys.exit(1)
        print(f"xel: {n} episode(s), all generated files up to date")
    else:
        print(f"xel: {n} episode(s); wrote {len(stale)} file(s)" + (": " + ", ".join(stale) if stale else ""))


if __name__ == "__main__":
    main()
