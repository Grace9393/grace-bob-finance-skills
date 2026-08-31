#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_report.py - QA gate for an IBM Carbon report page.

Checks the things that actually go wrong when one of these is handed to a
client: an external reference that dies behind their firewall, a palette that
has drifted off Carbon, an animation with no failsafe that prints blank, a
diagram with no alt text, a page that claims completeness it does not have.

    python check_report.py REPORT.html [more.html ...]
    python check_report.py REPORT.html --strict   # warnings fail too

Exit codes: 0 clean, 2 warnings only, 1 one or more failures.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys

__version__ = "1.0.0"

# Carbon v11 tokens the kit is built on. A hex outside this set means the
# palette has drifted - usually someone eyedropped a colour from a screenshot.
CARBON = {
    "#0F62FE", "#0043CE", "#002D9C", "#001141", "#CFE0FF",
    "#E5F6FF", "#BAE6FF", "#82CFFF",
    "#DA1E28", "#FFF1F1", "#198038", "#DEFBE6", "#D02670",
    "#8E6A00", "#FCF4D6",
    "#161616", "#393939", "#525252", "#6F6F6F",
    "#A8A8A8", "#D0D5DD", "#E0E0E0", "#F4F4F4", "#FFF", "#FFFFFF",
    # purple and teal ramps, used by the tag set
    "#6929C4", "#491D8B", "#F6F2FF", "#007D79", "#005D5D", "#D9FBFB",
    # borders the kit uses alongside the tag backgrounds
    "#FFD7D9", "#F1E0A8", "#A7F0BA", "#BAE6FF", "#E8DAFF",
}

EXTERNAL = re.compile(
    r"""(?:src|href)\s*=\s*["'](https?:)?//(?!fonts\.googleapis\.com|fonts\.gstatic\.com)""",
    re.I,
)


def check(path, strict=False):
    fails, warns = [], []
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    name = os.path.basename(path)
    # Commented-out markup is not shipped markup. Scanning it produces false
    # positives on any page whose skeleton documents itself.
    t = re.sub(r"<!--.*?-->", "", raw, flags=re.S)

    # --- self-contained ----------------------------------------------------
    ext = EXTERNAL.findall(t)
    if ext:
        fails.append("references %d external URL(s) - inline everything, the "
                     "client's network will not fetch them" % len(ext))
    for tag in ("<link ", "<iframe", "<object"):
        if tag in t.lower():
            fails.append("contains %s - the page must be one file" % tag.strip())

    # --- palette -----------------------------------------------------------
    # (?<!&) keeps HTML numeric entities out of it - &#183; is a middot, not a colour.
    hexes = set(
        h.upper()
        for h in re.findall(r"(?<!&)#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b", t)
    )
    drift = sorted(h for h in hexes if h not in CARBON)
    if drift:
        warns.append("%d colour(s) outside the Carbon token set: %s"
                     % (len(drift), ", ".join(drift[:8]) + (" ..." if len(drift) > 8 else "")))

    # --- typeface ----------------------------------------------------------
    if "IBM Plex" not in t:
        fails.append("IBM Plex Sans is not set - this is not the house face")

    # --- failsafes ---------------------------------------------------------
    if "IntersectionObserver" in t:
        if t.count("setTimeout") < 2:
            fails.append("uses IntersectionObserver with fewer than two failsafe "
                         "timeouts - content will print blank in browsers that "
                         "never fire the observer")
        if "data-w" in t and "getAttribute('data-w')" not in t.replace('"', "'"):
            warns.append("bars carry data-w but nothing reads it back")

    # --- print -------------------------------------------------------------
    if "@media print" not in t:
        fails.append("no print stylesheet - these get PDF'd for clients")
    elif "pagebreak" not in t:
        warns.append("print stylesheet present but no .pagebreak used - check "
                     "where sections land on the page")

    # --- accessibility -----------------------------------------------------
    svgs = re.findall(r"<svg\b[^>]*>", t, re.I)
    unlabelled = [s for s in svgs if "aria-label" not in s.lower() and "aria-labelledby" not in s.lower()]
    if unlabelled:
        warns.append("%d of %d <svg> have no aria-label" % (len(unlabelled), len(svgs)))
    if re.search(r"<img\b(?![^>]*\balt=)", t, re.I):
        warns.append("at least one <img> has no alt attribute")

    # --- structure ---------------------------------------------------------
    if '<div class="page"' not in t:
        warns.append("no .page wrapper - the 900px measure will not hold")
    h2s = re.findall(r'<h2\b([^>]*)>', t, re.I)
    if h2s:
        no_id = [h for h in h2s if "id=" not in h]
        if no_id and "secnav" in t:
            warns.append("%d of %d <h2> have no id, so the section nav cannot "
                         "link to them" % (len(no_id), len(h2s)))

    # --- provenance --------------------------------------------------------
    if not re.search(r"source|coverage|drawn from|built from", t, re.I):
        warns.append("no visible statement of what the page was built from")

    # --- house voice -------------------------------------------------------
    banned = ["leverage", "synergy", "synergies", "best-in-class", "world-class",
              "seamless", "cutting-edge", "game-chang", "revolutioni", "unlock the power",
              "robust solution", "holistic"]
    hit = sorted({b for b in banned if re.search(r"\b" + b, t, re.I)})
    if hit:
        warns.append("marketing words present: %s" % ", ".join(hit))

    ok = not fails and (not warns if strict else True)
    print("%s  %s" % ("PASS" if ok else ("FAIL" if fails else "WARN"), name))
    for f in fails:
        print("   x %s" % f)
    for w in warns:
        print("   ! %s" % w)
    return fails, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description="QA an IBM Carbon report page.")
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args(argv)

    any_fail = any_warn = False
    for p in args.reports:
        if not os.path.isfile(p):
            print("FAIL  %s\n   x not a file" % p)
            any_fail = True
            continue
        f, w = check(p, args.strict)
        any_fail = any_fail or bool(f)
        any_warn = any_warn or bool(w)

    if any_fail or (args.strict and any_warn):
        return 1
    return 2 if any_warn else 0


if __name__ == "__main__":
    sys.exit(main())
