#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_print.py - render a Carbon report through headless Chrome and check the
paper it produces.

`check_report.py` reads the markup. This one reads the output, which is the only
way to catch the defects that exist solely on paper: a page that quietly runs to
two sheets, a KPI tile that prints as 0 because its count-up never settled, or a
collapse marker leaking into the PDF.

Do not estimate height from the markup. It does not work - an estimator that
counted characters reported "98%, fits" for a document that printed to two pages.

    python check_print.py REPORT.html [--pages N] [--keep] [--pdf OUT.pdf]

When a page is over and you need to know by how much, bisect the sheet: render at
@page{size:210mm Nmm} for a few values of N and find the shortest sheet that still
gives one page. That is the true content height.

Exit codes: 0 as expected, 1 wrong page count or a print defect, 2 cannot render.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

__version__ = "1.0.0"

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    for b in BROWSERS:
        if os.path.isfile(b):
            return b
    for n in ("chrome", "google-chrome", "chromium", "msedge"):
        p = shutil.which(n)
        if p:
            return p
    return None


def file_url(path):
    p = os.path.abspath(path).replace(os.sep, "/")
    # '#' starts a URL fragment, and '#Client' style folders are real
    return "file:///" + p.replace("#", "%23").replace(" ", "%20")


def render(path, browser, out_pdf):
    # Delete any previous file at this path first. If the render silently fails -
    # and the browser-handoff case does exactly that - a stale PDF left in place
    # gets validated instead, and the tool reports PASS on a document it never
    # produced. A false pass is worse than a false failure.
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    started = time.time()
    cmd = [
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        # long enough for the kit's 2.5s print-settle backstop to fire
        "--virtual-time-budget=6000",
        "--print-to-pdf=" + out_pdf,
        file_url(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if os.path.isfile(out_pdf):
        # a file that predates this run is not this run's output
        if os.path.getmtime(out_pdf) < started - 1:
            return False, "the file at that path is older than this run - the render did not write it"
        # Chrome can return before the write is flushed; wait for the size to settle
        last, stable = -1, 0
        while stable < 3:
            size = os.path.getsize(out_pdf)
            if size == last and size > 0:
                stable += 1
            else:
                stable, last = 0, size
            time.sleep(0.2)
        return True, ""
    # Chrome exits 0 and writes nothing when a normal browser window is already
    # open: the launcher hands the command to that instance and --headless never
    # runs. Nothing in stderr says so, which makes it look like a broken page.
    try:
        v = subprocess.run([browser, "--version"], capture_output=True, text=True, timeout=30)
        blob = (v.stdout or "") + (v.stderr or "")
        if "existing browser session" in blob.lower():
            return False, ("the browser handed this command to an already-open window, "
                           "so headless never ran. Close the browser and retry, or point "
                           "--browser at a different one.")
    except Exception:
        pass
    return False, (proc.stderr or "").strip()[-400:] or "no output and no error from the browser"


def render_playwright(path, out_pdf):
    """Fallback renderer.

    The browser CLI is unreliable here: with an ordinary window open, Chrome
    hands --print-to-pdf to that instance and silently writes nothing. Playwright
    drives its own browser and is unaffected, so it is tried whenever the CLI
    produces no file.

    prefer_css_page_size makes the page's own @page rule win, which is what the
    CLI does and what the deliverable is laid out against."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright not installed"
    if os.path.exists(out_pdf):
        os.remove(out_pdf)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(file_url(path))
            page.wait_for_timeout(3000)   # let the 2.5s print-settle backstop fire
            page.pdf(path=out_pdf, print_background=True, prefer_css_page_size=True)
            browser.close()
    except Exception as exc:
        return False, "playwright failed: %s" % exc
    return os.path.isfile(out_pdf), ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a Carbon report and check the paper.")
    ap.add_argument("report")
    ap.add_argument("--pages", type=int, default=0,
                    help="expected page count; omit to report without asserting")
    ap.add_argument("--pdf", help="write the rendered PDF here and keep it")
    ap.add_argument("--keep", action="store_true", help="keep the temporary PDF and print its path")
    ap.add_argument("--browser", help="path to a specific Chrome or Edge binary")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.report):
        print("FAIL  not a file: %s" % args.report)
        return 2
    browser = args.browser or find_browser()
    if not browser:
        print("SKIP  no Chrome or Edge found - cannot render")
        return 2
    try:
        import pypdf
    except ImportError:
        print("SKIP  pypdf not installed (pip install pypdf) - cannot read the PDF")
        return 2

    tmp = tempfile.mkdtemp(prefix="carbon-print-")
    pdf = args.pdf or os.path.join(tmp, "render.pdf")
    ok, err = render(args.report, browser, pdf)
    if not ok:
        ok, perr = render_playwright(args.report, pdf)
        if ok:
            print("note  browser CLI unusable - rendered with Playwright instead")
        else:
            print("FAIL  render produced no PDF")
            print("      CLI        : %s" % err)
            print("      Playwright : %s" % perr)
            shutil.rmtree(tmp, ignore_errors=True)
            return 2

    source_html = open(args.report, encoding="utf-8", errors="replace").read()
    reader = pypdf.PdfReader(pdf)
    pages = len(reader.pages)
    whole = "\n".join((p.extract_text() or "") for p in reader.pages)

    problems = []
    if args.pages and pages != args.pages:
        problems.append("prints to %d page(s), expected %d" % (pages, args.pages))

    # A tile whose count-up never settled prints as 0 - but a deliverable is
    # allowed to have a KPI that genuinely is zero, so only the excess counts.
    authored_zeros = len(re.findall(r'class="num"[^>]*>\s*0\s*<', source_html))
    zeros = len(re.findall(r"(?m)^\s*0\s*$", whole))
    if zeros > authored_zeros:
        problems.append("%d KPI tile(s) printed as 0 but only %d are authored as 0 - "
                        "a count-up did not settle; check the print-correctness "
                        "addendum is present in the JS" % (zeros, authored_zeros))

    if re.search(r"\u2212\s*$", whole, re.M):
        problems.append("collapse marker printed - h2.collapsible::after is not hidden in print")

    box = reader.pages[0].mediabox
    size = "%.0f x %.0f mm" % (box.width / 72 * 25.4, box.height / 72 * 25.4)

    print("%s  %s" % ("FAIL" if problems else "PASS", os.path.basename(args.report)))
    print("      %d page(s), %s" % (pages, size))
    for p in problems:
        print("   x  %s" % p)
    if args.pdf:
        print("      pdf: %s" % args.pdf)
    elif args.keep:
        print("      pdf: %s" % pdf)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
