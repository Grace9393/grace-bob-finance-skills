"""AR KPI baseline calculator for the ar-diagnostic skill.

Reads invoice-level CSV (invoice_id, customer, amount, issue_date, due_date,
paid_date[, exception_category]) and prints a markdown baseline: DSO, BPDSO,
ADD, CEI, aging buckets, % over 90 days, exception counts.

Simplifications (state them in the findings report):
- Invoices are treated as fully paid on paid_date (no partial payments).
- DSO uses the simple ending-balance method over the analysis window.

Usage:
  python ar_kpi_baseline.py invoices.csv --asof 2026-06-30 [--window 180]
  python ar_kpi_baseline.py --make-sample
"""

import argparse
import csv
import datetime as dt
import pathlib
import random
import sys

BUCKETS = [("Current", 0), ("1-30", 30), ("31-60", 60), ("61-90", 90), ("90+", None)]
BENCH = {
    "DSO": "top quartile <=28-30d, median ~36-46d (Hackett/APQC)",
    "CEI": ">=80% healthy, >=85% strong",
    "PCT_OVER_90": "<3% product firms, <5% service firms",
}


def parse_date(s):
    return dt.date.fromisoformat(s.strip()) if s and s.strip() else None


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "invoice_id": r["invoice_id"],
                "customer": r.get("customer", ""),
                "amount": float(r["amount"]),
                "issue_date": parse_date(r["issue_date"]),
                "due_date": parse_date(r["due_date"]),
                "paid_date": parse_date(r.get("paid_date", "")),
                "exception_category": (r.get("exception_category") or "").strip(),
            })
    return rows


def open_amount(inv, on):
    """Amount outstanding on date `on` (full-payment simplification)."""
    if inv["issue_date"] > on:
        return 0.0
    if inv["paid_date"] and inv["paid_date"] <= on:
        return 0.0
    return inv["amount"]


def baseline(rows, asof, window_days):
    start = asof - dt.timedelta(days=window_days)
    credit_sales = sum(r["amount"] for r in rows if start < r["issue_date"] <= asof)
    beginning_ar = sum(open_amount(r, start) for r in rows)
    ending_ar = sum(open_amount(r, asof) for r in rows)
    ending_current = sum(open_amount(r, asof) for r in rows if r["due_date"] >= asof)

    dso = ending_ar / credit_sales * window_days if credit_sales else None
    bpdso = ending_current / credit_sales * window_days if credit_sales else None
    add = dso - bpdso if dso is not None else None
    cei_den = beginning_ar + credit_sales - ending_current
    cei = (beginning_ar + credit_sales - ending_ar) / cei_den * 100 if cei_den else None

    aging = {name: 0.0 for name, _ in BUCKETS}
    for r in rows:
        amt = open_amount(r, asof)
        if amt <= 0:
            continue
        past_due = (asof - r["due_date"]).days
        if past_due <= 0:
            aging["Current"] += amt
        elif past_due <= 30:
            aging["1-30"] += amt
        elif past_due <= 60:
            aging["31-60"] += amt
        elif past_due <= 90:
            aging["61-90"] += amt
        else:
            aging["90+"] += amt
    pct_over_90 = aging["90+"] / ending_ar * 100 if ending_ar else 0.0

    exceptions = {}
    for r in rows:
        if r["exception_category"] and open_amount(r, asof) > 0:
            exceptions[r["exception_category"]] = exceptions.get(r["exception_category"], 0) + 1

    return {
        "asof": asof, "window_days": window_days, "credit_sales": credit_sales,
        "ending_ar": ending_ar, "dso": dso, "bpdso": bpdso, "add": add, "cei": cei,
        "aging": aging, "pct_over_90": pct_over_90, "exceptions": exceptions,
        "open_invoices": sum(1 for r in rows if open_amount(r, asof) > 0),
    }


def fmt(v, suffix=""):
    return f"{v:,.1f}{suffix}" if v is not None else "n/a (no credit sales in window)"


def report(b):
    L = [f"# AR KPI Baseline — as of {b['asof']} (window: {b['window_days']} days)", ""]
    L.append("| Metric | Value | Benchmark |")
    L.append("|---|---|---|")
    L.append(f"| Credit sales in window | {b['credit_sales']:,.0f} | — |")
    L.append(f"| Ending AR ({b['open_invoices']} open invoices) | {b['ending_ar']:,.0f} | — |")
    L.append(f"| DSO | {fmt(b['dso'], ' days')} | {BENCH['DSO']} |")
    L.append(f"| Best Possible DSO | {fmt(b['bpdso'], ' days')} | gap vs DSO = overdue drag |")
    L.append(f"| ADD (DSO - BPDSO) | {fmt(b['add'], ' days')} | terms problem vs collection execution |")
    L.append(f"| CEI | {fmt(b['cei'], '%')} | {BENCH['CEI']} |")
    L.append(f"| % AR > 90 days past due | {b['pct_over_90']:,.1f}% | {BENCH['PCT_OVER_90']} |")
    L += ["", "## Aging buckets", "", "| Bucket | Open amount | Share |", "|---|---|---|"]
    for name, _ in BUCKETS:
        amt = b["aging"][name]
        share = amt / b["ending_ar"] * 100 if b["ending_ar"] else 0
        L.append(f"| {name} | {amt:,.0f} | {share:,.1f}% |")
    if b["exceptions"]:
        L += ["", "## Open invoices by exception category", ""]
        for k, v in sorted(b["exceptions"].items(), key=lambda x: -x[1]):
            L.append(f"- {k}: {v}")
    return "\n".join(L)


def make_sample(outdir="sample_data"):
    rng = random.Random(42)
    p = pathlib.Path(outdir)
    p.mkdir(exist_ok=True)
    cats = ["", "", "", "", "data", "system", "policy", "customer"]
    customers = [f"CUST-{i:03d}" for i in range(1, 21)]
    rows = []
    for i in range(1, 241):
        issue = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 180))
        terms = rng.choice([30, 30, 45, 60])
        due = issue + dt.timedelta(days=terms)
        lateness = rng.choice([-5, 0, 5, 12, 25, 40, 75, 120])
        paid = due + dt.timedelta(days=lateness)
        paid_str = paid.isoformat() if paid <= dt.date(2026, 6, 30) and rng.random() < 0.8 else ""
        rows.append([f"INV-{i:04d}", rng.choice(customers), round(rng.uniform(500, 25000), 2),
                     issue.isoformat(), due.isoformat(), paid_str,
                     rng.choice(cats) if not paid_str else ""])
    out = p / "invoices.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["invoice_id", "customer", "amount", "issue_date", "due_date", "paid_date", "exception_category"])
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} invoices)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", nargs="?", help="invoice-level CSV")
    ap.add_argument("--asof", default=None, help="analysis date YYYY-MM-DD (default: max date in data)")
    ap.add_argument("--window", type=int, default=180, help="analysis window in days (default 180)")
    ap.add_argument("--make-sample", action="store_true", help="generate sample_data/invoices.csv")
    args = ap.parse_args()

    if args.make_sample:
        make_sample()
        return
    if not args.csv_path:
        ap.error("csv_path required (or use --make-sample)")
    rows = load(args.csv_path)
    if not rows:
        sys.exit("no rows in input")
    asof = parse_date(args.asof) if args.asof else max(r["issue_date"] for r in rows)
    print(report(baseline(rows, asof, args.window)))


if __name__ == "__main__":
    main()
