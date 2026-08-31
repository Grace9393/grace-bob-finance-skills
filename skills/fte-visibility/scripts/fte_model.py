"""FTE Effort & Cost-Center Visibility — Proposal 4 (Monica).

Joins HR headcount, cost-center actuals, and project/timesheet allocations into the
effort model; surfaces the unallocated-FTE number; calls the ICA narrative agent;
exposes MCP tools so Bob answers effort questions directly.

Usage:
    python fte_model.py --headcount hc.csv --costcenters cc.csv --alloc alloc.csv
    python fte_model.py ... --narrate            # also call the ICA narrative agent
    python fte_model.py --serve                  # run as MCP server for Bob

Expected extracts (aggregate at cost-center level — no employee names needed):
    hc.csv    : employee_id, cost_center, fte
    cc.csv    : cost_center, cc_name, actual_cost, owner
    alloc.csv : employee_id, target (process or project), pct
"""

import argparse
import json
import os

import pandas as pd
import requests

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None

ICA_HOST = "https://servicesessentials.ibm.com"
OUT_DIR = os.environ.get("FTE_OUT", "model_out")


def build_model(headcount_csv, costcenter_csv, alloc_csv):
    hc = pd.read_csv(headcount_csv)
    cc = pd.read_csv(costcenter_csv)
    al = pd.read_csv(alloc_csv)

    m = hc.merge(al, on="employee_id", how="left")
    m["alloc_fte"] = m["fte"] * m["pct"].fillna(0) / 100.0

    effort = (m.dropna(subset=["target"]).groupby("target")["alloc_fte"]
              .sum().round(1).reset_index().rename(columns={"alloc_fte": "fte"})
              .sort_values("fte", ascending=False))

    # the invisibility number: people with no (or partial) work allocation
    m["unalloc_fte"] = m["fte"] * (100 - m.groupby("employee_id")["pct"].transform("sum").fillna(0)).clip(lower=0) / 100.0
    unallocated = (m.drop_duplicates("employee_id").groupby("cost_center")["unalloc_fte"]
                   .sum().round(1).reset_index().query("unalloc_fte > 0")
                   .sort_values("unalloc_fte", ascending=False))

    cc_fte = hc.groupby("cost_center")["fte"].sum().reset_index()
    cost = cc.merge(cc_fte, on="cost_center", how="left")
    cost["cost_per_fte"] = (cost["actual_cost"] / cost["fte"]).round(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    effort.to_csv(f"{OUT_DIR}/effort_by_target.csv", index=False)
    unallocated.to_csv(f"{OUT_DIR}/unallocated_fte.csv", index=False)
    cost.to_csv(f"{OUT_DIR}/cost_per_fte.csv", index=False)

    total_unalloc = float(unallocated["unalloc_fte"].sum())
    print(f"model written to {OUT_DIR}/ — unallocated FTE total: {total_unalloc:.1f}")
    return {"effort": effort, "unallocated": unallocated, "cost": cost,
            "total_unallocated_fte": total_unalloc}


def narrate(model, assistant_id=None):
    """Monthly narrative via the ICA agent — reviewed by a human before the client sees it.
    No ICA key? Writes the complete prompt to model_out/narrative_prompt.txt instead —
    paste it into Bob or an ICA assistant in the UI; the output contract is identical."""
    payload = {
        "effort_by_target": model["effort"].head(20).to_dict("records"),
        "unallocated_fte_by_cc": model["unallocated"].head(20).to_dict("records"),
        "cost_per_fte": model["cost"].head(20).to_dict("records"),
    }
    prompt = (
        "You are the FTE-visibility analyst. From this month's model output (JSON below):\n"
        "1) Effort by process/project — what changed vs. what you'd expect, top 5.\n"
        "2) The unallocated-FTE picture by cost center — state the total plainly; this is "
        "the number the client has never seen.\n"
        "3) Three reallocation recommendations with cost-per-FTE evidence.\n"
        "4) Data-quality flags (missing allocations, orphan cost centers) — flag, don't guess.\n"
        "Cite figures from the JSON only.\n\n" + json.dumps(payload)
    )
    if not os.environ.get("ICA_API_KEY"):
        path = f"{OUT_DIR}/narrative_prompt.txt"
        open(path, "w", encoding="utf-8").write(prompt)
        print(f"ICA_API_KEY not set — full prompt written to {path}; "
              "paste into Bob or an ICA assistant (Tier A path).")
        return prompt
    assistant_id = assistant_id or os.environ["FTE_ANALYST_AGENT"]
    r = requests.post(f"{ICA_HOST}/apis/v3/executePrompt",
                      headers={"Authorization": f"Bearer {os.environ['ICA_API_KEY']}"},
                      json={"assistantId": assistant_id, "prompt": prompt}, timeout=120)
    r.raise_for_status()
    text = r.json().get("response", r.json())
    open(f"{OUT_DIR}/narrative.md", "w", encoding="utf-8").write(str(text))
    print(f"narrative written to {OUT_DIR}/narrative.md — review before it reaches the client")
    return text


# ---------------- MCP tools (Bob answers effort questions directly) ----------------
mcp = FastMCP("fte-visibility") if FastMCP else None
tool = lambda f: f   # functions stay plain-callable; MCP registration happens in __main__


@tool
def effort_by_process(top: int = 20) -> list:
    """Allocated FTE by process/project, largest first."""
    return pd.read_csv(f"{OUT_DIR}/effort_by_target.csv").head(top).to_dict("records")


@tool
def unallocated_fte() -> list:
    """The invisibility number: FTE with no visible work allocation, by cost center."""
    return pd.read_csv(f"{OUT_DIR}/unallocated_fte.csv").to_dict("records")


@tool
def cost_per_fte(cost_center: str = "") -> list:
    """Cost per FTE by cost center (optionally one cost center)."""
    df = pd.read_csv(f"{OUT_DIR}/cost_per_fte.csv")
    if cost_center:
        df = df[df["cost_center"].astype(str) == cost_center]
    return df.to_dict("records")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--headcount"); ap.add_argument("--costcenters"); ap.add_argument("--alloc")
    ap.add_argument("--narrate", action="store_true")
    ap.add_argument("--serve", action="store_true")
    a = ap.parse_args()
    if a.serve:
        if not mcp:
            raise SystemExit("fastmcp not installed — pip install fastmcp")
        for f in (effort_by_process, unallocated_fte, cost_per_fte):
            mcp.tool()(f)   # register without replacing the module-level function
        mcp.run()
    else:
        model = build_model(a.headcount, a.costcenters, a.alloc)
        if a.narrate:
            narrate(model)
