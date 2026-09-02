#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure_blocks.py - which blocks are actually eating the page?

`fit_one_page.py` says you are 19mm over. This says where the 19mm is. Run it
before cutting a single word: the block you assume is the problem usually is
not, and layout is nearly always a better lever than wording.

    python measure_blocks.py REPORT.html
    python measure_blocks.py REPORT.html --width 188 --selector ".hero,.summary-box,h2,.row3"

**Set the viewport to the printed content width, not the browser's.** A block
measured in a 1280px window is far shorter than the same block in a 188mm
column, because the text reflows. Measuring at the default viewport reported a
193mm page for a document that genuinely needed 296mm, and the "fix" derived
from those numbers did nothing. --width is millimetres of *content* - sheet
width minus both margins - and defaults to A4 with 11mm margins.

Exit code: 0 always. This is an instrument, not a test.
"""

from __future__ import annotations

import argparse
import os
import sys

MM_PX = 96.0 / 25.4          # CSS px per mm at the standard 96dpi print mapping
DEFAULT_SELECTOR = (".hero,.summary-box,h2,p.muted,.row3,table,.source-box,"
                    ".footer,.kpi-strip,.wave,.block,.pain-card,.enh-card")

JS = """() => {
  const sel = %s;
  const seen = new Set();
  return [...document.querySelectorAll(sel)]
    .filter(e => e.offsetParent !== null && !e.closest('.screen-only'))
    .map(e => {
      const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
      // a child of an already-listed flex row is reported but not totalled, so
      // the sum stays honest when .row3 and its cards both match the selector
      let nested = false;
      for (const p of seen) if (p.contains(e)) nested = true;
      seen.add(e);
      return {
        name: (e.tagName.toLowerCase() + '.' + (e.className || '')).slice(0, 24),
        h: Math.round(r.height),
        mt: Math.round(parseFloat(cs.marginTop) || 0),
        mb: Math.round(parseFloat(cs.marginBottom) || 0),
        nested: nested,
        text: (e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 30)
      };
    });
}"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure printed block heights at true print width.")
    ap.add_argument("report")
    ap.add_argument("--width", type=float, default=188.0,
                    help="printed CONTENT width in mm (sheet minus both margins; default 188 = A4 - 2x11mm)")
    ap.add_argument("--selector", default=DEFAULT_SELECTOR)
    ap.add_argument("--settle", type=int, default=2600)
    args = ap.parse_args(argv)

    if not os.path.isfile(args.report):
        print("FAIL  not a file: %s" % args.report)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP  playwright not installed")
        return 2

    px = int(round(args.width * MM_PX))
    url = "file:///" + os.path.abspath(args.report).replace(os.sep, "/") \
        .replace("#", "%23").replace(" ", "%20")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": px, "height": 1400})
        page.goto(url)
        page.wait_for_timeout(args.settle)
        page.emulate_media(media="print")
        page.wait_for_timeout(250)
        rows = page.evaluate(JS % _js_str(args.selector))
        browser.close()

    if not rows:
        print("nothing matched %r outside .screen-only" % args.selector)
        return 0

    width = max(len(r["name"]) for r in rows)
    print("measured at %.0f mm content width (%d px)\n" % (args.width, px))
    print("%-*s %7s %7s  %s" % (width, "BLOCK", "mm", "share", "text"))
    print("-" * (width + 60))
    total = sum(r["h"] + r["mt"] + r["mb"] for r in rows if not r["nested"])
    for r in rows:
        mm = (r["h"] + r["mt"] + r["mb"]) / MM_PX
        share = "" if r["nested"] else "%5.1f%%" % (100.0 * (r["h"] + r["mt"] + r["mb"]) / total)
        mark = "  " if not r["nested"] else "+ "
        print("%s%-*s %6.1f %7s  %s" % (mark, width - 2, r["name"], mm, share, r["text"]))
    print("-" * (width + 60))
    print("%-*s %6.1f mm   (+ rows are inside another block and not totalled)"
          % (width, "TOTAL", total / MM_PX))
    print()
    print("Before trimming prose, check the cheaper levers:")
    print("  - an equal-width flex row is as tall as its fullest column; widening")
    print("    that one column shortens the whole band, and every band that shares")
    print("    the ratio, without losing a word")
    print("  - heading font-size and margins in @media print")
    print("  - a trailing margin under the last block, which buys mm for nothing")
    return 0


def _js_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


if __name__ == "__main__":
    sys.exit(main())
