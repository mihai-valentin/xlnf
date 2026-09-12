#!/usr/bin/env python3
"""Verify every note is registered everywhere it needs to be.

This site has no build step, so adding a note means editing four files by hand.
Forget one and the note is published but invisible — and the failure is silent,
which is the worst kind. This checks for that instead of trusting memory.

Usage:  python3 check-notes.py        # exits non-zero if anything is missing

Checks per note directory under notes/:
  1. listed in notes/index.html (the visible list)
  2. present in the blogPost[] array of notes/index.html's JSON-LD
  3. present in sitemap.xml
  4. present in llms.txt
  5. its own canonical URL matches its actual path
  6. has a title, a meta description, and parseable JSON-LD
Also flags entries in those files that point at a note directory which no
longer exists.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://mihai-valentin.github.io/xlnf"

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

    print(f"checked {len(slugs)} note(s): " + ", ".join(slugs))


if __name__ == "__main__":
    main()
    if problems:
        print("\nFAIL")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("all notes registered in notes/index.html, sitemap.xml and llms.txt")
