"""MCP server for the Finance Exception Resolution Agent — Proposal 1.

Exposes governed tools to Bob: aging queries, task creation (ServiceNow), follow-up
drafting, and the monthly reduce-analysis feed. Nothing sends or executes without the
AAS workflow's human approval gate having released the action list.

Run:      python exception_mcp.py            (stdio MCP server; register in Bob)
Fallback: if your Bob build has no MCP support, call the same functions via
          `python -c "..."` from Bob's Bash tool — they are plain functions.

Env: SNOW_INSTANCE, SNOW_USER, SNOW_TOKEN (ServiceNow dev sandbox), REGISTER_CSV.
"""

import os
from datetime import date

import pandas as pd
import requests

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - CLI fallback mode
    FastMCP = None

REGISTER = os.environ.get("REGISTER_CSV", "exception_register.csv")
SNOW = os.environ.get("SNOW_INSTANCE", "https://devXXXX.service-now.com")
SNOW_AUTH = (os.environ.get("SNOW_USER", ""), os.environ.get("SNOW_TOKEN", ""))

mcp = FastMCP("finance-exceptions") if FastMCP else None
tool = lambda f: f   # functions stay plain-callable; MCP registration happens in __main__


def _load() -> pd.DataFrame:
    return pd.read_csv(REGISTER)


@tool
def list_open_exceptions(process: str = "", min_age_days: int = 0) -> list:
    """Open exceptions, optionally filtered by process area (OTC, PTP, RTR, FPA) and minimum age."""
    df = _load()
    df = df[df["status"].str.upper() == "OPEN"]
    if process:
        df = df[df["process"].str.upper() == process.upper()]
    if min_age_days:
        df = df[df["age_days"].fillna(0) >= min_age_days]
    return df.sort_values("age_days", ascending=False).to_dict("records")


@tool
def aging_summary() -> list:
    """Aging buckets by process area — the one-picture view that doesn't exist today."""
    df = _load()
    df = df[df["status"].str.upper() == "OPEN"].copy()
    df["bucket"] = pd.cut(df["age_days"].fillna(0), [-1, 7, 30, 60, 10_000],
                          labels=["0-7d", "8-30d", "31-60d", "60d+"])
    out = df.groupby(["process", "bucket"], observed=True).agg(
        count=("ref", "size"), amount=("amount", "sum")).reset_index()
    return out.to_dict("records")


@tool
def create_task(ref: str, owner: str, action: str, approved_by: str) -> dict:
    """Create a routed task for an APPROVED exception action.
    approved_by is required — the AAS gate's approver name goes on the record.
    With ServiceNow credentials set, posts to ServiceNow; without them, appends to the
    local task queue (task_queue.csv) — same contract, zero external dependency."""
    if not approved_by:
        return {"error": "refused: no approver recorded — actions only run post-gate"}
    if not SNOW_AUTH[1]:   # Tier A: no sandbox needed — local queue is the demo path
        row = pd.DataFrame([{"task_id": f"LOCAL-{pd.Timestamp.now():%H%M%S}", "ref": ref,
                             "owner": owner, "action": action,
                             "approved_by": approved_by, "created": str(date.today())}])
        row.to_csv("task_queue.csv", mode="a", index=False,
                   header=not os.path.exists("task_queue.csv"))
        return {"created": row.iloc[0]["task_id"], "ref": ref, "mode": "local-queue"}
    r = requests.post(f"{SNOW}/api/now/table/task", auth=SNOW_AUTH, timeout=60,
                      json={"short_description": f"[{ref}] {action}",
                            "description": f"Exception {ref}. Approved by {approved_by} on {date.today()}.",
                            "assigned_to": owner})
    r.raise_for_status()
    return {"created": r.json().get("result", {}).get("number"), "ref": ref, "mode": "servicenow"}


@tool
def draft_followup(ref: str) -> str:
    """Draft (never send) the follow-up email for one exception; the owner sends it."""
    df = _load()
    row = df[df["ref"].astype(str) == str(ref)]
    if row.empty:
        return f"No exception with ref {ref} in the register."
    r = row.iloc[0]
    return (f"Subject: Action needed — {r['type']} exception {r['ref']} ({r['process']}, "
            f"{int(r['age_days'] or 0)} days old)\n\n"
            f"Hi {r['owner'] or 'team'},\n\n"
            f"{r['detail'] or 'This exception'} is still open and aging. "
            f"Amount involved: {r['amount']}. Could you resolve or reassign by end of week?\n\n"
            f"(Drafted by the exception agent; reviewed before sending.)")


@tool
def reduce_analysis_feed(months: int = 3) -> list:
    """Closed-exception history for the monthly root-cause clustering run (Bob analyzes this)."""
    df = _load()
    closed = df[df["status"].str.upper() != "OPEN"]
    return closed.groupby(["process", "type"]).agg(
        count=("ref", "size"), avg_age=("age_days", "mean"), amount=("amount", "sum")
    ).reset_index().sort_values("count", ascending=False).to_dict("records")


TOOLS = (list_open_exceptions, aging_summary, create_task, draft_followup, reduce_analysis_feed)

if __name__ == "__main__":
    if mcp:
        for f in TOOLS:
            mcp.tool()(f)   # register without replacing the module-level function
        mcp.run()
    else:
        print("fastmcp not installed — CLI mode. Example:")
        print(pd.DataFrame(aging_summary()))
