#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_source_coverage.py - did the synthesis drop anything?

A one-pager exists to compress. Compression is not the risk; silent loss is. A
source report lists nine pain points and the page states three findings - that
is good work if all nine are inside the three, and a quiet omission if they are
not. Nobody can tell the difference by reading, which is why this is a script.

Each item from the source is reported against the page in four ways, and they
are not equivalent:

  substance on print   the printed sheet says what the item actually is. The
                       only kind a reader gets from paper alone.
  named on print       the printed sheet cites the item's id but not its
                       content - honest, and much weaker.
  screen layer         it is in an interactive layer that print drops.
  ** ABSENT **         nowhere. Either put it back or decide to drop it.

Usage:

    python audit_source_coverage.py CONFIG.json [PAGE.html]

CONFIG.json:

    {
      "source":        "…/analysis.html",
      "item_selector": ".pain-card .pain-title",
      "id_pattern":    "(P\\\\d)\\\\s*[—–-]\\\\s*(.+)",
      "page":          "…/onepager.html",
      "diagnosis_ends_at": "h2#fix",
      "evidence": {
        "P1": ["escalation", "named individual"],
        "P7": ["ZD45 credit", "applied as the remedy"]
      }
    }

`diagnosis_ends_at` is the point where the page stops diagnosing and starts
prescribing. Everything after it is excluded from the substance test, because a
pain point mentioned in the solution ("duplicate checks move into scripting") is
a fix, not a diagnosis - counting it lets the page claim coverage it has not
earned. Leaving this out reported 8 of 9 covered when the truth was 6 of 9.

Exit codes: 0 every item is accounted for, 1 at least one is absent.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

from bs4 import BeautifulSoup


def text_of(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True))


def load_items(cfg):
    soup = BeautifulSoup(io.open(cfg["source"], encoding="utf-8", errors="replace").read(), "lxml")
    rx = re.compile(cfg["id_pattern"])
    items = []
    for el in soup.select(cfg["item_selector"]):
        m = rx.search(text_of(el))
        if m:
            items.append((m.group(1), m.group(2).strip()))
    return items


def split_page(path, cut_selector):
    """Return (printed diagnosis, printed whole, screen layer) as plain text."""
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(raw, "lxml")
    for t in soup.select("style, script"):
        t.decompose()
    screen = " ".join(text_of(t) for t in soup.select(".screen-only"))
    for t in soup.select(".screen-only, .topnav, .totop"):
        t.decompose()
    printed = text_of(soup)

    diagnosis = printed
    if cut_selector:
        cut = soup.select_one(cut_selector)
        if cut is not None:
            for el in list(cut.find_all_next()) + [cut]:
                el.extract()
            diagnosis = text_of(soup)
    return diagnosis, printed, screen


def risky(pattern):
    """Patterns that quietly match inside longer words under re.I.

    A bare three-letter acronym is the usual offender: "OAR" matched inside
    "dashboard" and passed an item the page never mentioned."""
    bare = re.fullmatch(r"[A-Z]{2,5}", pattern)
    return bool(bare)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check nothing from the source was silently dropped.")
    ap.add_argument("config")
    ap.add_argument("page", nargs="?")
    ap.add_argument("--strict-ids", action="store_true",
                    help="require substance, not just a cited id, to count as covered")
    args = ap.parse_args(argv)

    cfg = json.loads(io.open(args.config, encoding="utf-8").read())
    page = args.page or cfg.get("page")
    for key, val in (("source", cfg.get("source")), ("page", page)):
        if not val or not os.path.isfile(val):
            print("FAIL  %s not found: %s" % (key, val))
            return 2

    items = load_items(cfg)
    if not items:
        print("FAIL  %r matched nothing in the source - check item_selector and id_pattern"
              % cfg["item_selector"])
        return 2

    diagnosis, printed, screen = split_page(page, cfg.get("diagnosis_ends_at"))
    evidence = cfg.get("evidence", {})

    warned = [p for pats in evidence.values() for p in pats if risky(p)]
    if warned:
        print("note  these patterns match inside longer words under re.I - anchor them")
        print("      with \\b or they will pass items the page never states:")
        for p in sorted(set(warned)):
            print("        %s" % p)
        print()

    rows, absent = [], []
    for iid, title in items:
        pats = evidence.get(iid, [])
        sub = any(re.search(p, diagnosis, re.I) for p in pats)
        named = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(iid), printed) is not None
        seen = any(re.search(p, screen, re.I) for p in pats) or \
            re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(iid), screen) is not None
        where = ", ".join(w for w, ok in (("substance on print", sub),
                                          ("named on print", named),
                                          ("screen layer", seen)) if ok)
        covered = sub if args.strict_ids else (sub or named or seen)
        if not where:
            where = "** ABSENT **"
        rows.append((iid, title, where))
        if not covered:
            absent.append((iid, title))
        if not pats:
            rows[-1] = (iid, title, where + "   (no evidence pattern configured)")

    width = max(len(t) for _, t, _ in rows)
    print("%-6s %-*s  %s" % ("ID", width, "SOURCE ITEM", "WHERE ON THE PAGE"))
    print("-" * (9 + width + 40))
    for iid, title, where in rows:
        print("%-6s %-*s  %s" % (iid, width, title, where))

    print()
    print("  items in the source          : %d" % len(rows))
    print("  substance on the printed page: %d" % sum(1 for r in rows if "substance" in r[2]))
    print("  named by id on the print     : %d" % sum(1 for r in rows if "named" in r[2]))
    print("  in the screen layer          : %d" % sum(1 for r in rows if "screen" in r[2]))
    print("  ABSENT                       : %d" % len(absent))
    for iid, title in absent:
        print("     - %-6s %s" % (iid, title))
    return 1 if absent else 0


if __name__ == "__main__":
    sys.exit(main())
