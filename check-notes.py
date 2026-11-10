#!/usr/bin/env python3
"""Verify every note is registered everywhere it needs to be.

This site has no build step, so adding a note means editing five files by hand.
Forget one and the note is published but invisible — and the failure is silent,
which is the worst kind. This checks for that instead of trusting memory.

Usage:  python3 check-notes.py        # exits non-zero if anything is missing

Checks per note directory under notes/:
  1. listed in notes/index.html (the visible list)
  2. present in the blogPost[] array of notes/index.html's JSON-LD
  3. present in sitemap.xml
  4. present in llms.txt
  5. present in llm.html (the list AND its ItemList JSON-LD)
  6. its own canonical URL matches its actual path
  7. has a title, a meta description, and parseable JSON-LD
Also flags entries in those files that point at a note directory which no
longer exists, and an ItemList numberOfItems that disagrees with reality.

Then the same for /xel/ (Xel's room), which is its own collection, not notes:
  - every xel/<slug>/ has an episode.json and is registered in xel/index.html,
    sitemap.xml, llms.txt and llm.html (list + "Xel's room — episodes" ItemList)
  - index.html links to xel/
  - no registry references an episode that doesn't exist
  - every generated file is current (runs `xel-build.py --check`)
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://xlnf.dev"

problems = []


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def main():
    slugs = sorted(
        os.path.basename(os.path.dirname(p))
        for p in glob.glob(os.path.join(ROOT, "notes", "*", "index.html"))
    )
    if not slugs:
        problems.append("no notes found under notes/*/index.html")
        return

    index = read("notes/index.html")
    sitemap = read("sitemap.xml")
    llms = read("llms.txt")
    llm_page = read("llm.html")

    # the ItemList in llm.html — the machine-readable half of the agent surface
    listed_for_agents = set()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', llm_page, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            problems.append(f"llm.html: unparseable JSON-LD ({e})")
            continue
        if data.get("@type") == "ItemList":
            items = data.get("itemListElement", [])
            for item in items:
                m = re.search(r"/notes/([^/]+)/", item.get("url", ""))
                if m:
                    listed_for_agents.add(m.group(1))
            declared = data.get("numberOfItems")
            if declared is not None and declared != len(items):
                problems.append(
                    f"llm.html: ItemList numberOfItems is {declared} but it holds {len(items)} items"
                )

    # the blogPost array, from the Blog JSON-LD block
    posted = set()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', index, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as e:
            problems.append(f"notes/index.html: unparseable JSON-LD ({e})")
            continue
        if data.get("@type") == "Blog":
            for post in data.get("blogPost", []):
                m = re.search(r"/notes/([^/]+)/", post.get("url", ""))
                if m:
                    posted.add(m.group(1))

    for slug in slugs:
        page = read(f"notes/{slug}/index.html")

        if f'href="{slug}/"' not in index:
            problems.append(f"{slug}: not linked from the list in notes/index.html")
        if slug not in posted:
            problems.append(f"{slug}: missing from blogPost[] in notes/index.html JSON-LD")
        if f"{BASE}/notes/{slug}/" not in sitemap:
            problems.append(f"{slug}: missing from sitemap.xml")
        if f"notes/{slug}/" not in llms:
            problems.append(f"{slug}: missing from llms.txt")
        if f'href="notes/{slug}/"' not in llm_page:
            problems.append(f"{slug}: not linked from the list in llm.html")
        if slug not in listed_for_agents:
            problems.append(f"{slug}: missing from the ItemList JSON-LD in llm.html")

        canonical = re.search(r'<link rel="canonical" href="([^"]+)"', page)
        if not canonical:
            problems.append(f"{slug}: no canonical URL")
        elif canonical.group(1) != f"{BASE}/notes/{slug}/":
            problems.append(
                f"{slug}: canonical points at {canonical.group(1)}, expected {BASE}/notes/{slug}/"
            )

        if not re.search(r"<title>.+</title>", page):
            problems.append(f"{slug}: no <title>")
        desc = re.search(r'<meta name="description" content="([^"]*)"', page)
        if not desc or not desc.group(1).strip():
            problems.append(f"{slug}: no meta description")
        elif len(desc.group(1)) > 200:
            problems.append(f"{slug}: meta description is {len(desc.group(1))} chars (keep under ~160)")

        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                problems.append(f"{slug}: unparseable JSON-LD ({e})")

    # the other direction: references to notes that no longer exist.
    # Slug-shaped only — a looser pattern also matches the notes index URL
    # itself ("/notes/</loc>") and reports a note called "<".
    SLUG = r"([a-z0-9][a-z0-9-]*)"
    for ref in set(re.findall(rf"/notes/{SLUG}/", sitemap)):
        if ref not in slugs:
            problems.append(f"sitemap.xml references notes/{ref}/ which does not exist")
    for ref in set(re.findall(rf"\(notes/{SLUG}/\)", llms)):
        if ref not in slugs:
            problems.append(f"llms.txt references notes/{ref}/ which does not exist")
    for ref in set(re.findall(rf'href="notes/{SLUG}/"', llm_page)):
        if ref not in slugs:
            problems.append(f"llm.html references notes/{ref}/ which does not exist")
    for ref in listed_for_agents - set(slugs):
        problems.append(f"llm.html ItemList references notes/{ref}/ which does not exist")

    print(f"checked {len(slugs)} note(s): " + ", ".join(slugs))


def check_xel():
    """/xel/ episodes: registered everywhere, and generated files not stale."""
    if not os.path.isdir(os.path.join(ROOT, "xel")):
        return
    dirs = sorted(
        d for d in os.listdir(os.path.join(ROOT, "xel"))
        if os.path.isdir(os.path.join(ROOT, "xel", d))
    )
    slugs = []
    for d in dirs:
        if not os.path.isfile(os.path.join(ROOT, "xel", d, "episode.json")):
            problems.append(f"xel/{d}/: no episode.json (pages are generated from it)")
        else:
            slugs.append(d)

    xel_index = read("xel/index.html")
    sitemap = read("sitemap.xml")
    llms = read("llms.txt")
    llm_page = read("llm.html")
    home = read("index.html")

    if 'href="xel/"' not in home:
        problems.append("index.html: no link to xel/")
    if f"{BASE}/xel/</loc>" not in sitemap:
        problems.append("sitemap.xml: missing the /xel/ landing page")

    listed = set()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', llm_page, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue  # already reported by the notes pass
        if data.get("@type") == "ItemList" and data.get("name") == "Xel's room — episodes":
            for item in data.get("itemListElement", []):
                m = re.search(r"/xel/([^/]+)/", item.get("url", ""))
                if m:
                    listed.add(m.group(1))

    for slug in slugs:
        if f'href="{slug}/"' not in xel_index:
            problems.append(f"xel/{slug}: not listed in xel/index.html")
        if f"{BASE}/xel/{slug}/" not in sitemap:
            problems.append(f"xel/{slug}: missing from sitemap.xml")
        if f"(xel/{slug}/)" not in llms:
            problems.append(f"xel/{slug}: missing from llms.txt")
        if f'href="xel/{slug}/"' not in llm_page:
            problems.append(f"xel/{slug}: not linked from the list in llm.html")
        if slug not in listed:
            problems.append(f"xel/{slug}: missing from the Xel's room ItemList in llm.html")

    SLUG = r"([a-z0-9][a-z0-9-]*)"
    for name, text, pat in (
        ("sitemap.xml", sitemap, rf"/xel/{SLUG}/"),
        ("llms.txt", llms, rf"\(xel/{SLUG}/\)"),
        ("llm.html", llm_page, rf'href="xel/{SLUG}/"'),
        ("xel/index.html", xel_index, rf'href="{SLUG}/"'),
    ):
        for ref in set(re.findall(pat, text)):
            if ref not in slugs:
                problems.append(f"{name} references xel/{ref}/ which does not exist")

    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "xel-build.py"), "--check"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        problems.append("xel-build.py --check failed:\n" + r.stdout.strip())
    print(f"checked {len(slugs)} xel episode(s): " + ", ".join(slugs))


if __name__ == "__main__":
    main()
    check_xel()
    if problems:
        print("\nFAIL")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("all notes registered in notes/index.html, sitemap.xml, llms.txt and llm.html")
    print("all xel episodes registered in xel/index.html, sitemap.xml, llms.txt and llm.html; generated files current")
