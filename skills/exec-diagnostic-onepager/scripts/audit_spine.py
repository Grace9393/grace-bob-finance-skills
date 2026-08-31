#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_spine.py - do the parts of the page tell one story?

A four-part diagnostic states a problem, names the pains, gives their root
causes and sketches the fix. Those four only work as one argument if the same
named threads run through all of them, in the same order, under the same words.
That is the part a reader notices immediately and a writer loses silently: add a
fourth pain and the root-cause section still has three; reword one label and the
correspondence quietly breaks.

So the page carries an explicit spine - A, B, C - printed in every part, and
this checks it. Keys are found wherever a run of text begins with a single
capital followed by a separator, which is the convention the skill prescribes:

    <div class="pain-title">A &middot; Single points of failure</div>
    <div class="wave-t">A &rarr; Wave 1</div>
    <strong>A &middot; single points of failure</strong>

    python audit_spine.py PAGE.html
    python audit_spine.py PAGE.html --sections problem,pain,cause,fix

Sections are the `<h2 id>` values that must agree, in page order, plus the text
before the first heading. Screen-only layers are excluded: a spine that only
lines up on screen does not line up on the sheet that reaches the room.

Exit codes: 0 the parts agree, 1 they do not.
"""

from __future__ import annotations

import argparse
import re
import sys

from bs4 import BeautifulSoup

# A key is one capital letter, then a separator that is not ordinary punctuation
# in running prose. "A." and "A," are excluded on purpose - they appear mid
# sentence constantly and would fabricate keys out of nothing.
KEY = re.compile(r"^\s*([A-Z])\s*(?:·|→|–|—|->|⇒)\s*(.+)$")
TITLEISH = ".pain-title,.wave-t,.enh-title,.block-title,.reg-head,h3,h4,strong,b,td>strong"


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def keys_and_labels(nodes):
    """Ordered, de-duplicated (key, label) pairs from a run of elements."""
    out, seen = [], set()
    for el in nodes:
        m = KEY.match(norm(el.get_text(" ", strip=True)))
        if not m:
            continue
        k, label = m.group(1), norm(m.group(2))
        if k in seen:
            continue
        seen.add(k)
        out.append((k, label))
    return out


def doc_order(soup):
    """Position of every tag in document order.

    `sourceline` looks like the obvious key and is not: the parser leaves it
    unset on nodes it synthesises, and decompose() drops it entirely, so
    comparing two of them raises on None. A single walk is exact and cheap."""
    return {id(el): i for i, el in enumerate(soup.descendants) if getattr(el, "name", None)}


def section_of(el, heads, order):
    """Which <h2 id> this element sits under, by document order."""
    pos = order.get(id(el), -1)
    current = None
    for h in heads:
        if order.get(id(h), 1 << 30) < pos:
            current = h
        else:
            break
    return current


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check one spine runs through every part.")
    ap.add_argument("page")
    ap.add_argument("--sections", help="comma-separated <h2 id> values, in page order; "
                                       "default is every id outside the screen layer")
    ap.add_argument("--lead", default="problem",
                    help="id of the standfirst block that opens the argument (default: problem)")
    ap.add_argument("--spine-from", default="pain",
                    help="the section whose spine the others must match (default: pain)")
    args = ap.parse_args(argv)

    soup = BeautifulSoup(open(args.page, encoding="utf-8", errors="replace").read(), "lxml")
    for t in soup.select("style, script"):
        t.decompose()
    # Strip with the parser. A regex that tries to match nested divs runs past
    # its own closing tag and eats the body, and every part then reports empty -
    # a false negative indistinguishable from a real one.
    for t in soup.select(".screen-only, .topnav, .totop"):
        t.decompose()

    order = doc_order(soup)
    heads = [h for h in soup.find_all("h2") if h.get("id")]
    wanted = args.sections.split(",") if args.sections else [h["id"] for h in heads]

    parts = []
    lead = soup.select_one("#" + args.lead)
    if lead is not None and args.lead not in wanted:
        wanted.insert(0, args.lead)
    for sid in wanted:
        if lead is not None and sid == args.lead:
            parts.append((sid, keys_and_labels(lead.select(TITLEISH))))
            continue
        head = next((h for h in heads if h["id"] == sid), None)
        if head is None:
            print("FAIL  no <h2 id=\"%s\"> on the page" % sid)
            return 1
        nodes = [el for el in soup.select(TITLEISH) if section_of(el, heads, order) is head]
        parts.append((sid, keys_and_labels(nodes)))

    width = max(len(s) for s, _ in parts)
    print("%-*s  %s" % (width, "PART", "SPINE"))
    print("-" * (width + 26))
    for sid, pairs in parts:
        print("%-*s  %s" % (width, sid, " ".join(k for k, _ in pairs) or "** none **"))

    ref = dict(parts).get(args.spine_from, [])
    ref_keys = [k for k, _ in ref]
    problems = []
    if not ref_keys:
        problems.append("section %r carries no keys - there is nothing to align to" % args.spine_from)
    for sid, pairs in parts:
        got = [k for k, _ in pairs]
        if got != ref_keys:
            problems.append("%s is [%s], %s is [%s]"
                            % (sid, " ".join(got) or "empty", args.spine_from, " ".join(ref_keys)))

    if ref_keys:
        print()
        cols = [sid for sid, _ in parts]
        print("%-4s %s" % ("KEY", "  |  ".join("%-26s" % c for c in cols)))
        print("-" * (5 + 31 * len(cols)))
        lookup = {sid: dict(pairs) for sid, pairs in parts}
        for k in ref_keys:
            print("%-4s %s" % (k, "  |  ".join("%-26s" % (lookup[c].get(k, "--")[:26]) for c in cols)))
        # Labels only have to match where both parts name the thing rather than
        # its remedy: "A - Single points of failure" against "A - Wave 1" is a
        # correct pairing, not a drift, so compare the diagnostic parts only.
        diag = [c for c in cols if c not in (args.lead,)][:2]
        if len(diag) == 2:
            for k in ref_keys:
                x, y = lookup[diag[0]].get(k, ""), lookup[diag[1]].get(k, "")
                if x and y and x.rstrip(".").lower() != y.rstrip(".").lower():
                    problems.append("key %s reads %r in %s and %r in %s"
                                    % (k, x, diag[0], y, diag[1]))

    print()
    if problems:
        print("FAIL  the parts do not line up")
        for p in problems:
            print("   x  %s" % p)
        return 1
    print("PASS  %d parts, one %d-item spine, same order, same labels"
          % (len(parts), len(ref_keys)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
