#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_page_tokens.py - is anything on this page not in the sources?

`audit_source_coverage.py` runs source to page and asks what was dropped. This
runs page to source and asks what was invented. Both directions are needed, and
this is the one that catches the expensive failure: a plausible number nobody
can trace, sitting in a client deliverable.

It takes no curated claim list. A hand-written list of claims drifts from the
page it describes, and drifts silently. This pulls every factual token off the
rendered page instead - money, percentages, system codes, dates, durations,
named accounts - and asks whether the sources contain each one. Tokens cannot
drift from the page they were extracted from.

    python audit_page_tokens.py PAGE.html --source D1=rules.html --source D2=analysis.html
    python audit_page_tokens.py PAGE.html --source-dir ./sources --ours CA10,NBS

Three outcomes per token:

  traced      a source contains it
  declared    the page itself marks it - `.src.calc` for a figure counted off a
              source table, `.src.ours` for a recommendation no source makes.
              A marked derivation is provenance, not an orphan, and calling it
              one would make the tool contradict the artifact.
  orphan      neither. Fix the page or mark it.

Exit codes: 0 everything traces or is declared, 1 something is neither.
"""

from __future__ import annotations

import argparse
import glob
import html as H
import io
import os
import re
import sys

PATTERNS = [
    # [0-9,.]* would swallow the comma in "$150, with a separate rule"; requiring
    # a digit after any separator stops the token at the number
    ("money",    r"\$\s?[0-9](?:[0-9]|[,.][0-9])*\s?[KkMmBb]?"),
    ("percent",  r"\b\d{1,3}(?:\.\d+)?%"),
    ("code",     r"\b(?:Z[A-Z]{2,4}\d?|VA0\d|FBL5N|OTR|OAR|FSCM|ZRF)\b"),
    ("duration", r"\b\d{1,3}\s?(?:months?|days?|hours?|hrs?|weeks?|years?)\b"),
    ("date",     r"\b(?:January|February|March|April|May|June|July|August|September|"
                 r"October|November|December)\s+\d{4}\b"),
    ("year",     r"\b(?:19|20)\d{2}\b"),
    ("system",   r"\b(?:SAP|EDI|UOM|SLA|KPI|DSO|Celonis|MyInvenio|Power ?BI|ServiceNow|"
                 r"Esker|High ?Radius|Serrala|Coupa|Blackline)\b"),
    # (?<![$\d.,]) keeps this off the tail of a money token: "$100 rule" is one
    # fact the money pattern already has, not a count of a hundred rules
    ("count",    r"(?<![$\d.,])\b\d{1,4} (?:SOPs?|accounts?|rules?|decisions?|decision points?|"
                 r"FTEs?|gaps?|workarounds?|items?)\b"),
]


def plain(path):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"<style.*?</style>|<script.*?</script>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t)))


def page_text(path):
    """The whole body, screen layer included - an interactive block still needs
    a source, and only its layout is ours.

    Tags collapse to a newline, not a space, and the patterns above all join
    their parts with a literal space. A token therefore cannot span two
    elements. Flattening with a space invents facts out of adjacency: a card
    ending "…Last Updated Jan 2020" beside a separate "gap" badge reads as the
    token "2020 gap", which is in no source because nobody wrote it."""
    t = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"<style.*?</style>|<script.*?</script>", " ", t, flags=re.S)
    body = re.search(r"<body[^>]*>(.*)</body>", t, re.S)
    flat = re.sub(r"<[^>]+>", "\n", body.group(1) if body else t)
    return re.sub(r"[ \t]+", " ", H.unescape(flat))


def declared(path):
    """Text the page itself marks as derived or as ours."""
    t = io.open(path, encoding="utf-8", errors="replace").read()
    out = {"calc": "", "ours": ""}
    for kind in out:
        for m in re.finditer(r'class="src %s"' % kind, t):
            chunk = t[max(0, m.start() - 400):m.start()]
            out[kind] += " " + re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", chunk)))
    return out


def variants(tok):
    """The ways one figure gets written across documents."""
    alts = {tok, tok.replace(" ", ""), tok.replace("blocks ", "block "),
            tok.replace("block ", "blocks "), tok.replace("hrs", "hours"),
            tok.replace("hours", "hrs")}
    if tok.startswith("$"):
        n = tok.lstrip("$").strip()
        alts |= {"$" + n, n}
        if n[-1:].upper() in ("K", "M"):
            base, mult = n[:-1], {"K": "000", "M": "000000"}[n[-1:].upper()]
            alts |= {base + "," + mult[:3] if mult == "000" else base + mult, base + mult}
    return alts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check every factual token on the page traces to a source.")
    ap.add_argument("page")
    ap.add_argument("--source", action="append", default=[], metavar="CODE=PATH",
                    help="a source document, e.g. D1=rules.html; repeatable")
    ap.add_argument("--source-dir", help="use every .html/.md/.txt in this directory, named by filename")
    ap.add_argument("--ours", default="", help="comma-separated tokens that are page furniture "
                                               "(engagement codes, client name) and need no source")
    args = ap.parse_args(argv)

    docs = {}
    for pair in args.source:
        code, _, path = pair.partition("=")
        if not path or not os.path.isfile(path):
            print("FAIL  source not found: %s" % pair)
            return 2
        docs[code] = plain(path)
    if args.source_dir:
        for path in sorted(glob.glob(os.path.join(args.source_dir, "*"))):
            if os.path.splitext(path)[1].lower() in (".html", ".htm", ".md", ".txt"):
                docs[os.path.splitext(os.path.basename(path))[0][:12]] = plain(path)
    if not docs:
        print("FAIL  no sources given - pass --source CODE=PATH or --source-dir")
        return 2

    ours = {s.strip() for s in args.ours.split(",") if s.strip()} | set(docs)
    text = page_text(args.page)
    marks = declared(args.page)

    found = {}
    for label, rx in PATTERNS:
        for m in re.finditer(rx, text):
            tok = m.group(0).strip()
            if len(tok) < 2 or tok in ours:
                continue
            found.setdefault(tok, label)

    rows, orphans = [], []
    for tok in sorted(found, key=lambda s: (found[s], s.lower())):
        alts = variants(tok)
        hits = [c for c in sorted(docs) if any(a.lower() in docs[c].lower() for a in alts)]
        if not hits:
            for kind, label in (("calc", "declared: counted"), ("ours", "declared: ours")):
                if tok.lower() in marks[kind].lower():
                    hits = [label]
                    break
        rows.append((found[tok], tok, hits))
        if not hits:
            orphans.append((found[tok], tok))

    if not rows:
        print("no factual tokens matched - check the page is the built file, not the template")
        return 0

    width = max(len(t) for _, t, _ in rows)
    print("%-9s %-*s  %s" % ("KIND", width, "TOKEN ON THE PAGE", "IN WHICH SOURCE"))
    print("-" * (12 + width + 20))
    for kind, tok, hits in rows:
        print("%-9s %-*s  %s" % (kind, width, tok, ", ".join(hits) if hits else "** none **"))

    n_declared = sum(1 for _, _, h in rows if h and h[0].startswith("declared"))
    print()
    print("  tokens checked                          : %d" % len(rows))
    print("  traced to a source                      : %d"
          % sum(1 for _, _, h in rows if h and not h[0].startswith("declared")))
    print("  declared on the page as derived or ours : %d" % n_declared)
    print("  NOT in sources and NOT declared         : %d" % len(orphans))
    for kind, tok in orphans:
        print("     - %-8s %s" % (kind, tok))
    return 1 if orphans else 0


if __name__ == "__main__":
    sys.exit(main())
