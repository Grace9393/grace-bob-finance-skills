#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scan a folder tree of Excel workbooks for keywords, in sheet names and cell values.

Use this to locate an existing CRM / partner list / pipeline inside a messy folder
before building anything new — the answer is usually already on disk under a name
nobody remembers.

    python scan_excel_keywords.py "C:/path/to/folder" -k CRM 合作對象 自媒體
    python scan_excel_keywords.py "." -k KOL --json hits.json

Notes
-----
* Reads with data_only=True, so formula cells yield their cached value. A workbook
  never opened in Excel since the formula was written yields None; that is reported
  as a miss, not an error.
* Caps the scan at --max-rows / --max-cols per sheet for speed. Raise them if a
  target list sits far down a sheet.
* Unreadable workbooks (password-protected, corrupt, legacy .xls) are collected and
  reported at the end rather than aborting the run.
"""
import argparse
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required:  pip install openpyxl")

EXTS = (".xlsx", ".xlsm")


def scan_workbook(path, keywords, max_rows, max_cols):
    """Return {sheet_name: [hit labels]} for one workbook."""
    hits = {}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            found = set()
            for kw in keywords:
                if kw.lower() in ws.title.lower():
                    found.add("SHEETNAME:" + kw)
            try:
                rows = ws.iter_rows(min_row=1, max_row=max_rows,
                                    max_col=max_cols, values_only=True)
                for row in rows:
                    for value in row:
                        if value is None:
                            continue
                        text = str(value)
                        low = text.lower()
                        for kw in keywords:
                            if kw.lower() in low:
                                found.add(kw)
                    # every keyword already seen in a sheet name and a cell -> stop early
                    if len(found) >= len(keywords) * 2:
                        break
            except Exception:
                # a single unreadable sheet must not sink the workbook
                pass
            if found:
                hits[ws.title] = sorted(found)
    finally:
        wb.close()
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="folder to scan (recursive)")
    ap.add_argument("-k", "--keywords", nargs="+", required=True,
                    help="keywords; matching is case-insensitive substring")
    ap.add_argument("--max-rows", type=int, default=300)
    ap.add_argument("--max-cols", type=int, default=60)
    ap.add_argument("--json", help="also write results to this JSON path")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        sys.exit(f"not a folder: {args.root}")

    results, errors, scanned = [], [], 0
    for dirpath, _dirnames, filenames in os.walk(args.root):
        for fn in filenames:
            if not fn.lower().endswith(EXTS) or fn.startswith("~$"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, args.root)
            scanned += 1
            try:
                hits = scan_workbook(path, args.keywords, args.max_rows, args.max_cols)
            except Exception as exc:
                errors.append({"file": rel, "error": str(exc)[:160]})
                continue
            if hits:
                results.append({"file": rel, "sheets": hits})

    print(f"=== scanned {scanned} workbooks under {args.root} ===")
    print(f"=== {len(results)} with hits ===\n")
    for r in results:
        print(f"[{r['file']}]")
        for sheet, kws in r["sheets"].items():
            print(f"    sheet '{sheet}': {', '.join(kws)}")
        print()

    if errors:
        print(f"=== {len(errors)} unreadable (reported, not fatal) ===")
        for e in errors:
            print(f"  {e['file']}: {e['error']}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"scanned": scanned, "hits": results, "errors": errors},
                      fh, ensure_ascii=False, indent=2)
        print(f"\nwrote {args.json}")

    # A sheet NAMED for the keyword is a far stronger signal than a stray cell match.
    strong = [r["file"] for r in results
              if any(any(k.startswith("SHEETNAME:") for k in kws)
                     for kws in r["sheets"].values())]
    if strong:
        print("\n*** sheet-name matches (look here first) ***")
        for f in strong:
            print("   ", f)


if __name__ == "__main__":
    main()
