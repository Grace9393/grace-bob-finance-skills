"""Hank — MCP server for the FP&A Digital Advisor (Proposal 2).

Governed tools over the `pnl` DuckDB fact table: cut data any way, rank variances,
run what-ifs, and feed the weekly brief. Bob + this server + the persona prompt
below = Hank, the digital teammate.

Run:      python hank_mcp.py      (stdio MCP server; register in Bob)
Fallback: functions are plain Python — callable from Bob's Bash tool without MCP.

PERSONA PROMPT (paste as Bob's system/context when registering Hank):
    You are Hank, our FP&A teammate. Use the tools for every number — never invent
    or extrapolate figures. When asked for a cut, return the table plus two sentences
    on what stands out. When asked for advice, rank by variance impact and cite the
    rows behind every claim. If coverage is thin (few rows, many nulls), say so
    before answering. Tone: colleague, not chatbot; concise, concrete, no filler.
"""

import os

import duckdb

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None

DB = os.environ.get("HANK_DB", "fpna.duckdb")
mcp = FastMCP("hank-fpna") if FastMCP else None
tool = lambda f: f   # functions stay plain-callable; MCP registration happens in __main__

DIMS = {"entity", "region", "product", "account", "month"}
MEASURES = {"actual", "budget", "py"}


def _con():
    return duckdb.connect(DB, read_only=True)


@tool
def describe_data() -> dict:
    """Coverage check: months, entities, row count, null share per measure. Hank cites this when data is thin."""
    con = _con()
    n, months, entities = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT month), COUNT(DISTINCT entity) FROM pnl").fetchone()
    nulls = {m: con.execute(f"SELECT ROUND(100.0*SUM({m} IS NULL)/COUNT(*),1) FROM pnl").fetchone()[0]
             for m in MEASURES}
    return {"rows": n, "months": months, "entities": entities, "pct_null": nulls}


@tool
def cut_data(dimensions: list, measures: list, filters: str = "", limit: int = 200) -> list:
    """Cut the P&L any way. dimensions from: entity, region, product, account, month.
    measures from: actual, budget, py. filters: SQL WHERE fragment, e.g. "month LIKE '2026-Q2%' AND region='EMEA'"."""
    dims = [d for d in dimensions if d in DIMS]
    meas = [m for m in measures if m in MEASURES]
    if not dims or not meas:
        return [{"error": f"dimensions must be in {sorted(DIMS)}, measures in {sorted(MEASURES)}"}]
    q = (f"SELECT {', '.join(dims)}, "
         f"{', '.join(f'ROUND(SUM({m}),0) AS {m}' for m in meas)} FROM pnl "
         f"{'WHERE ' + filters if filters else ''} GROUP BY ALL ORDER BY 1 LIMIT {int(limit)}")
    return _con().execute(q).df().to_dict("records")


@tool
def top_variances(n: int = 10, by: str = "account", filters: str = "") -> list:
    """Largest actual-vs-budget variances — the 'biggest risks' starting point.
    by: any dimension (account, entity, region, product)."""
    if by not in DIMS:
        return [{"error": f"by must be one of {sorted(DIMS)}"}]
    q = (f"SELECT {by}, ROUND(SUM(actual-budget),0) AS variance, "
         f"ROUND(100.0*SUM(actual-budget)/NULLIF(SUM(budget),0),1) AS pct_of_budget, "
         f"COUNT(*) AS rows_behind FROM pnl {'WHERE ' + filters if filters else ''} "
         f"GROUP BY ALL ORDER BY ABS(variance) DESC LIMIT {int(n)}")
    return _con().execute(q).df().to_dict("records")


@tool
def run_scenario(driver: str, change_pct: float, filters: str = "") -> dict:
    """What-if: apply a % change to a driver family and return the P&L impact vs. budget.
    driver: 'revenue' (accounts starting 4), 'cogs' (5), 'opex' (6) — adjust to the client's chart."""
    prefix = {"revenue": "4", "cogs": "5", "opex": "6"}.get(driver.lower())
    if not prefix:
        return {"error": "driver must be revenue, cogs, or opex"}
    con = _con()
    where = f"account LIKE '{prefix}%'" + (f" AND ({filters})" if filters else "")
    base, bud = con.execute(f"SELECT SUM(actual), SUM(budget) FROM pnl WHERE {where}").fetchone()
    base, bud = base or 0.0, bud or 0.0
    flexed = base * (1 + change_pct / 100.0)
    return {"driver": driver, "change_pct": change_pct,
            "base_actual": round(base), "flexed": round(flexed),
            "impact": round(flexed - base), "vs_budget_after": round(flexed - bud)}


@tool
def weekly_brief_feed() -> dict:
    """Everything the AAS weekly-brief workflow needs in one call: coverage, top 10 variances, biggest movers."""
    return {"coverage": describe_data(),
            "top_variances": top_variances(10),
            "by_region": top_variances(5, by="region")}


TOOLS = (describe_data, cut_data, top_variances, run_scenario, weekly_brief_feed)

if __name__ == "__main__":
    if mcp:
        for f in TOOLS:
            mcp.tool()(f)   # register without replacing the module-level function
        mcp.run()
    else:
        import pandas as pd
        print("fastmcp not installed — CLI mode. Coverage:")
        print(pd.Series(describe_data()))
