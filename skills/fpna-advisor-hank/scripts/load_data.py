"""Hank data loader — Proposal 2 (FP&A Digital Advisor).

Lands FP&A data in one queryable DuckDB star schema (`pnl` fact table) from either:
  - Planning Analytics (TM1 REST API view export)  → the asset-based path
  - ERP/EPM extracts (xlsx/csv)                    → the mid-tier / no-EPM path

Usage:
    python load_data.py --xlsx actuals.xlsx budget.xlsx
    python load_data.py --tm1-cube "Financials" --tm1-view "FP&A Export"
"""

import argparse
import os

import duckdb
import pandas as pd
import requests

DB = os.environ.get("HANK_DB", "fpna.duckdb")
TM1 = os.environ.get("TM1_HOST", "https://pa-host:8010/api/v1")
TM1_AUTH = (os.environ.get("TM1_USER", ""), os.environ.get("TM1_PASSWORD", ""))

PNL_COLS = ["entity", "region", "product", "account", "month", "scenario", "value"]


def from_xlsx(paths):
    frames = []
    for p in paths:
        df = pd.read_excel(p)
        df.columns = [c.strip().lower() for c in df.columns]
        missing = [c for c in PNL_COLS if c not in df.columns]
        if missing:
            raise SystemExit(f"{p}: missing columns {missing} — ask Bob to map them first.")
        frames.append(df[PNL_COLS])
    return pd.concat(frames, ignore_index=True)


def from_tm1(cube, view):
    """Execute a TM1 view and flatten cells; requires the view's title/row dims to
    align to the pnl schema (set up once in PA — this is the touchless-forecasting cube)."""
    r = requests.get(f"{TM1}/Cubes('{cube}')/Views('{view}')/tm1.Execute?$expand="
                     "Axes($expand=Hierarchies($select=Name),Tuples($expand=Members($select=Name))),"
                     "Cells($select=Ordinal,Value)",
                     auth=TM1_AUTH, verify=False, timeout=300)
    r.raise_for_status()
    data = r.json()
    cols = [h["Name"].lower() for ax in data["Axes"] for h in ax["Hierarchies"]]
    tuples = [[m["Name"] for m in t["Members"]] for ax in data["Axes"] for t in ax["Tuples"]]
    cells = data["Cells"]
    rows = []
    n_col_tuples = len(data["Axes"][0]["Tuples"]) or 1
    for c in cells:
        i = c["Ordinal"]
        row_t = tuples[n_col_tuples + i // n_col_tuples] if len(tuples) > n_col_tuples else []
        col_t = tuples[i % n_col_tuples]
        rows.append(dict(zip(cols, col_t + row_t), value=c["Value"]))
    df = pd.DataFrame(rows)
    return df.rename(columns={"version": "scenario", "period": "month"})[
        [c for c in PNL_COLS if c in df.columns] + ["value"]].dropna(subset=["value"])


def pivot_scenarios(long_df: pd.DataFrame) -> pd.DataFrame:
    """long (scenario column) -> wide fact table: actual / budget / py per row."""
    wide = long_df.pivot_table(index=["entity", "region", "product", "account", "month"],
                               columns="scenario", values="value", aggfunc="sum").reset_index()
    wide.columns = [str(c).strip().lower().replace(" ", "_") for c in wide.columns]
    for want, aliases in {"actual": ["actual", "act"], "budget": ["budget", "bud", "plan"],
                          "py": ["py", "prior_year", "ly"]}.items():
        for a in aliases:
            if a in wide.columns:
                wide = wide.rename(columns={a: want})
                break
        if want not in wide.columns:
            wide[want] = None
    return wide


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", nargs="*", default=[])
    ap.add_argument("--tm1-cube"); ap.add_argument("--tm1-view")
    a = ap.parse_args()

    long_df = from_tm1(a.tm1_cube, a.tm1_view) if a.tm1_cube else from_xlsx(a.xlsx)
    fact = pivot_scenarios(long_df)
    con = duckdb.connect(DB)
    con.execute("CREATE OR REPLACE TABLE pnl AS SELECT * FROM fact")
    n, = con.execute("SELECT COUNT(*) FROM pnl").fetchone()
    print(f"{DB}: pnl table loaded, {n} rows "
          f"({fact['month'].nunique()} months, {fact['entity'].nunique()} entities)")
