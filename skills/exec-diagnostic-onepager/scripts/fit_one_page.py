#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fit_one_page.py - how far over one page is this document, in millimetres?

`check_print.py` answers "one page or two". That is the wrong question while you
are still cutting: it tells you that you failed, not by how much, so you trim
blind and re-render. This renders the page onto a sheet of variable height and
bisects for the shortest sheet that still holds one page. The answer is the true
content height, and the difference from A4 is exactly the budget you have to find.

    python fit_one_page.py REPORT.html
    python fit_one_page.py REPORT.html --page-css "@page{size:A4;margin:11mm}"

Typical output:

    content needs 290 mm   A4 is 297 mm   ->  headroom 7 mm

Do not estimate height from the markup instead. A character-count estimator
reported "98%, fits" for a document that printed to two pages, which is worse
than no estimate because it is believed.

Exit codes: 0 it fits, 1 it is over, 2 cannot render.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tempfile

DEFAULT_PAGE_CSS = "@page{size:A4;margin:11mm}"
SHEETS = {"A4": (210, 297), "LETTER": (216, 279), "A3": (297, 420)}


def render_pages(browser, html, tmp, width_mm, height_mm, page_css, settle):
    """Render at a sheet of the given height and return the page count."""
    swapped = html.replace(page_css, "@page{size:%dmm %dmm;margin:11mm}" % (width_mm, height_mm))
    if swapped == html:
        raise SystemExit(
            "could not find the @page rule to substitute.\n"
            "  looked for : %s\n"
            "  pass the exact rule your file uses with --page-css" % page_css)
    path = os.path.join(tmp, "probe-%d.html" % height_mm)
    io.open(path, "w", encoding="utf-8").write(swapped)
    page = browser.new_page()
    page.goto("file:///" + path.replace(os.sep, "/"))
    page.wait_for_timeout(settle)
    pdf = os.path.join(tmp, "probe-%d.pdf" % height_mm)
    page.pdf(path=pdf, print_background=True, prefer_css_page_size=True)
    page.close()
    import pypdf
    return len(pypdf.PdfReader(pdf).pages)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure a document's true printed height.")
    ap.add_argument("report")
    ap.add_argument("--page-css", default=DEFAULT_PAGE_CSS,
                    help="the @page rule in the file, substituted during probing")
    ap.add_argument("--sheet", default="A4", choices=sorted(SHEETS),
                    help="sheet to compare against (default A4)")
    ap.add_argument("--pages", type=int, default=1,
                    help="how many sheets the document is allowed (default 1)")
    ap.add_argument("--settle", type=int, default=2600,
                    help="ms to wait for the kit's print-settle backstop (default 2600)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.report):
        print("FAIL  not a file: %s" % args.report)
        return 2
    try:
        from playwright.sync_api import sync_playwright
        import pypdf  # noqa: F401
    except ImportError as exc:
        print("SKIP  %s - pip install playwright pypdf && playwright install chromium" % exc)
        return 2

    width_mm, sheet_mm = SHEETS[args.sheet]
    budget = sheet_mm * args.pages
    html = io.open(args.report, encoding="utf-8", errors="replace").read()
    tmp = tempfile.mkdtemp(prefix="fit-one-page-")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        def fits(h):
            return render_pages(browser, html, tmp, width_mm, h, args.page_css,
                                args.settle) <= args.pages

        # Bracket first. An unbounded upper guess wastes renders, and a lower
        # bound that already fits means the document is far inside its budget.
        lo, hi = 120, budget
        if fits(lo):
            hi = lo
        else:
            while not fits(hi):
                lo, hi = hi, hi * 2
                if hi > 20000:
                    print("FAIL  the document does not fit any sheet under 20 m - "
                          "something is forcing a break")
                    browser.close()
                    return 2
            while hi - lo > 2:
                mid = (lo + hi) // 2
                if fits(mid):
                    hi = mid
                else:
                    lo = mid
        browser.close()

    over = hi - budget
    if not args.quiet:
        print("  content needs %d mm   %s x%d is %d mm   ->  %s %d mm"
              % (hi, args.sheet, args.pages, budget,
                 "OVER by" if over > 0 else "headroom", abs(over)))
        if 0 >= over > -5:
            print("  a sheet with under 5mm to spare is one font substitution away from")
            print("  spilling. Buy a little more before calling it done.")
    else:
        print(over)
    return 1 if over > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
