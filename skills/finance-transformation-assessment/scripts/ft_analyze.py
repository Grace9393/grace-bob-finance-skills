"""Finance transformation assessment analytics.

Three subcommands, each writing markdown (for the deck) and JSON (for ft_workbook.py):

    python ft_analyze.py gap      <client-metrics.csv>       [--industry X] [--realisation 0.7]
    python ft_analyze.py score    <capability-assessment.csv>
    python ft_analyze.py roadmap  <initiative-backlog.csv>   [--discount-rate 0.10] [--years 5]
    python ft_analyze.py all      --assets <dir>

Standard library only. Every output states the formula it used so a client can audit it.
"""

import argparse
import csv
import json
import os
import sys

# Markdown output carries non-ASCII punctuation; Windows consoles and redirected output
# default to cp1252 and would raise UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BENCHMARKS = os.path.join(HERE, "..", "assets", "benchmarks.csv")

WAVE_START_MONTH = {1: 0, 2: 6, 3: 18}
RAMP = [(3, 0.0), (6, 0.25), (12, 0.60)]  # months since go-live -> % of steady state; else 100%
BENEFIT_CATEGORIES = ["hard", "cost_avoidance", "working_capital", "productivity", "risk", "revenue"]


# ---------------------------------------------------------------- helpers

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [row for row in csv.DictReader(fh)]


def num(value, default=None):
    """Parse a CSV cell to float; blank/garbage returns default rather than raising."""
    if value is None:
        return default
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def money(value):
    if value is None:
        return "-"
    return "{:,.0f}".format(value)


def write_outputs(outdir, name, markdown, payload):
    os.makedirs(outdir, exist_ok=True)
    md_path = os.path.join(outdir, name + ".md")
    json_path = os.path.join(outdir, name + ".json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(markdown)
    print("\nwrote {} and {}".format(md_path, json_path))


# ---------------------------------------------------------------- gap analysis

def load_benchmarks(path):
    """Return {(metric_id, industry): row}."""
    table = {}
    for row in read_csv(path):
        table[(row["metric_id"].strip(), row["industry"].strip())] = row
    return table


def pick_benchmark(table, metric_id, industry):
    """Industry row if present, else cross-industry. Returns (row, fell_back)."""
    exact = table.get((metric_id, industry))
    if exact and (num(exact.get("median")) is not None or num(exact.get("top_quartile")) is not None):
        return exact, False
    fallback = table.get((metric_id, "cross-industry"))
    return fallback, fallback is not None and industry != "cross-industry"


def quartile_position(client, top, median, bottom, direction):
    better = (lambda a, b: a <= b) if direction == "lower_better" else (lambda a, b: a >= b)
    if top is not None and better(client, top):
        return "top quartile"
    if median is not None and better(client, median):
        return "second quartile"
    if bottom is not None and better(client, bottom):
        return "third quartile"
    if bottom is not None:
        return "bottom quartile"
    if median is not None:
        return "below median"
    if top is not None:
        return "outside top quartile"
    return "not classified"


def run_gap(args):
    benchmarks = load_benchmarks(args.benchmarks)
    rows, warnings = [], []

    for client_row in read_csv(args.metrics):
        metric_id = client_row["metric_id"].strip()
        client_value = num(client_row.get("client_value"))
        if client_value is None:
            warnings.append("{}: no client value - excluded".format(metric_id))
            continue

        bench, fell_back = pick_benchmark(benchmarks, metric_id, args.industry)
        if bench is None:
            warnings.append("{}: no benchmark row - reported without comparison".format(metric_id))
            rows.append({"metric_id": metric_id, "metric": metric_id, "client_value": client_value,
                         "benchmark_found": False})
            continue

        direction = bench.get("direction", "lower_better").strip() or "lower_better"
        top = num(bench.get("top_quartile"))
        median = num(bench.get("median"))
        bottom = num(bench.get("bottom_quartile"))
        sign = 1.0 if direction == "lower_better" else -1.0

        gap_median = (client_value - median) * sign if median is not None else None
        gap_top = (client_value - top) * sign if top is not None else None

        driver = num(client_row.get("driver_volume"))
        confidence = (bench.get("confidence") or "directional").strip()
        value_median = value_top = None
        if driver is not None and confidence == "verified":
            if gap_median is not None and gap_median > 0:
                value_median = gap_median * driver * args.realisation
            if gap_top is not None and gap_top > 0:
                value_top = gap_top * driver * args.realisation
        elif driver is not None and confidence != "verified":
            warnings.append(
                "{}: benchmark is DIRECTIONAL - value at stake suppressed, do not present a "
                "figure for this metric".format(metric_id))

        if fell_back:
            warnings.append("{}: no '{}' benchmark row - used cross-industry (label it on the page)"
                            .format(metric_id, args.industry))

        rows.append({
            "metric_id": metric_id,
            "metric": bench.get("metric", metric_id),
            "unit": bench.get("unit", ""),
            "industry_used": "cross-industry" if fell_back else args.industry,
            "client_value": client_value,
            "top_quartile": top,
            "median": median,
            "bottom_quartile": bottom,
            "direction": direction,
            "gap_to_median": gap_median,
            "gap_to_top": gap_top,
            "position": quartile_position(client_value, top, median, bottom, direction),
            "driver_volume": driver,
            "driver_description": client_row.get("driver_description", ""),
            "value_basis": client_row.get("value_basis", ""),
            "value_at_stake_to_median": value_median,
            "value_at_stake_to_top": value_top,
            "confidence": confidence,
            "source": bench.get("source", ""),
            "as_of": bench.get("as_of", ""),
            "population": bench.get("population", ""),
            "benchmark_found": True,
        })

    recurring = sum(r.get("value_at_stake_to_top") or 0 for r in rows
                    if r.get("value_basis") == "recurring_annual")
    one_time = sum(r.get("value_at_stake_to_top") or 0 for r in rows
                   if r.get("value_basis") == "one_time_cash")

    lines = ["# Benchmark gap and value at stake", "",
             "Realisation factor applied: **{:.0%}**. Industry requested: **{}**.".format(
                 args.realisation, args.industry), "",
             "| Metric | Client | Median | Top quartile | Position | Gap to median | Gap to top | "
             "Value at stake (to top) | Confidence | Source (as of) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r.get("benchmark_found"):
            lines.append("| {} | {} | - | - | no benchmark | - | - | - | - | - |".format(
                r["metric"], r["client_value"]))
            continue
        lines.append("| {} ({}) | {} | {} | {} | {} | {} | {} | {} | {} | {} ({}) |".format(
            r["metric"], r["unit"], r["client_value"],
            "-" if r["median"] is None else r["median"],
            "-" if r["top_quartile"] is None else r["top_quartile"],
            r["position"],
            "-" if r["gap_to_median"] is None else round(r["gap_to_median"], 2),
            "-" if r["gap_to_top"] is None else round(r["gap_to_top"], 2),
            money(r["value_at_stake_to_top"]),
            r["confidence"], r["source"], r["as_of"]))

    lines += ["", "## Value at stake summary", "",
              "- Recurring annual (gap to top quartile, after realisation): **${}**".format(money(recurring)),
              "- One-time cash release (working capital): **${}**".format(money(one_time)),
              "",
              "> Value at stake is the theoretical size of the prize, not the business case. "
              "Keep the two on separate pages (benchmark-library.md 3).",
              "", "Formula: `gap x driver_volume x realisation`. Driver per metric:", ""]
    for r in rows:
        if r.get("driver_volume"):
            lines.append("- **{}**: {} = {}".format(r["metric"], r["driver_description"],
                                                    money(r["driver_volume"])))

    if warnings:
        lines += ["", "## Warnings", ""] + ["- " + w for w in warnings]

    write_outputs(args.outdir, "benchmark_gap", "\n".join(lines),
                  {"realisation": args.realisation, "industry": args.industry, "rows": rows,
                   "recurring_annual_total": recurring, "one_time_cash_total": one_time,
                   "warnings": warnings})


# ---------------------------------------------------------------- maturity scoring

def run_score(args):
    rows = read_csv(args.assessment)
    lenses, capabilities = [], []
    cells = {}
    for row in rows:
        cap = row["capability"].strip()
        lens = row["lens"].strip().lower()
        if cap not in capabilities:
            capabilities.append(cap)
        if lens not in lenses:
            lenses.append(lens)
        cells[(cap, lens)] = {
            "current": num(row.get("current_level"), 0.0),
            "target": num(row.get("target_level"), 0.0),
            "weight": num(row.get("weight"), 1.0),
            "evidence": row.get("evidence", ""),
            "owner": row.get("owner", ""),
            "process_l2": row.get("process_l2", ""),
        }

    def weighted(items):
        total_w = sum(i["weight"] for i in items) or 1.0
        return (sum(i["current"] * i["weight"] for i in items) / total_w,
                sum(i["target"] * i["weight"] for i in items) / total_w)

    by_capability = {}
    for cap in capabilities:
        items = [cells[(cap, l)] for l in lenses if (cap, l) in cells]
        cur, tgt = weighted(items)
        by_capability[cap] = {"current": round(cur, 2), "target": round(tgt, 2),
                              "gap": round(tgt - cur, 2)}

    by_lens = {}
    for lens in lenses:
        items = [cells[(c, lens)] for c in capabilities if (c, lens) in cells]
        cur, tgt = weighted(items)
        by_lens[lens] = {"current": round(cur, 2), "target": round(tgt, 2),
                         "gap": round(tgt - cur, 2)}

    all_items = list(cells.values())
    overall_cur, overall_tgt = weighted(all_items)

    lines = ["# Capability maturity assessment", "",
             "Scale 1 Ad hoc - 2 Repeatable - 3 Defined - 4 Managed - 5 Optimised "
             "(target-operating-model.md 4). A level is only awarded where the client evidenced it.",
             "", "## Heatmap - current level (target in brackets)", "",
             "| Capability | " + " | ".join(l.title() for l in lenses) + " | Weighted | Gap |",
             "|---" * (len(lenses) + 3) + "|"]
    for cap in capabilities:
        cells_out = []
        for lens in lenses:
            c = cells.get((cap, lens))
            cells_out.append("-" if c is None else "{:g} ({:g})".format(c["current"], c["target"]))
        lines.append("| {} | {} | {:.2f} | {:.2f} |".format(
            cap, " | ".join(cells_out), by_capability[cap]["current"], by_capability[cap]["gap"]))
    lines.append("| **By lens** | " + " | ".join(
        "**{:.2f}**".format(by_lens[l]["current"]) for l in lenses)
        + " | **{:.2f}** | **{:.2f}** |".format(overall_cur, overall_tgt - overall_cur))

    weakest_lens = min(by_lens, key=lambda l: by_lens[l]["current"])
    largest_gap = max(by_capability, key=lambda c: by_capability[c]["gap"])
    lines += ["", "## Observations", "",
              "- Overall weighted maturity **{:.2f}** against a target of **{:.2f}** "
              "(gap {:.2f}).".format(overall_cur, overall_tgt, overall_tgt - overall_cur),
              "- Weakest lens: **{}** at {:.2f}.".format(weakest_lens.title(),
                                                         by_lens[weakest_lens]["current"]),
              "- Largest capability gap: **{}** ({:.2f}).".format(largest_gap,
                                                                  by_capability[largest_gap]["gap"]),
              "",
              "> Self-reported maturity typically runs about a level high. State on the page "
              "whether each level was evidenced or asserted."]

    write_outputs(args.outdir, "maturity", "\n".join(lines),
                  {"capabilities": capabilities, "lenses": lenses,
                   "cells": {"{}||{}".format(c, l): v for (c, l), v in cells.items()},
                   "by_capability": by_capability, "by_lens": by_lens,
                   "overall": {"current": round(overall_cur, 2), "target": round(overall_tgt, 2)}})


# ---------------------------------------------------------------- roadmap and business case

def ramp_pct(months_since_golive):
    if months_since_golive <= 0:
        return 0.0
    for boundary, pct in RAMP:
        if months_since_golive <= boundary:
            return pct
    return 1.0


def run_roadmap(args):
    rows = read_csv(args.initiatives)
    inits = {}
    order = []
    for row in rows:
        iid = row["id"].strip()
        order.append(iid)
        inits[iid] = {
            "id": iid,
            "name": row.get("name", ""),
            "type": (row.get("type") or "").strip(),
            "lens": (row.get("lens") or "").strip(),
            "benefit_category": (row.get("benefit_category") or "").strip(),
            "benefit_annual": num(row.get("benefit_annual"), 0.0),
            "cost_onetime": num(row.get("cost_onetime"), 0.0),
            "cost_run_annual": num(row.get("cost_run_annual"), 0.0),
            "effort": num(row.get("effort"), 3.0),
            "impact": num(row.get("impact"), 3.0),
            "duration_months": max(1, int(num(row.get("duration_months"), 6.0))),
            "depends_on": [d.strip() for d in (row.get("depends_on") or "").split(";") if d.strip()],
            "owner": row.get("owner", ""),
            "wave": int(num(row.get("wave"), 1.0)),
            "pain_point_ids": row.get("pain_point_ids", ""),
        }

    warnings = []
    for iid, ini in inits.items():
        for dep in ini["depends_on"]:
            if dep not in inits:
                warnings.append("{}: depends on unknown initiative '{}'".format(iid, dep))
            elif inits[dep]["wave"] > ini["wave"]:
                warnings.append(
                    "{} (wave {}) depends on {} (wave {}) - dependency violates the wave plan; "
                    "resequence rather than assuming it resolves itself".format(
                        iid, ini["wave"], dep, inits[dep]["wave"]))
        if not ini["pain_point_ids"].strip():
            warnings.append("{}: not traced to any pain point - confirm it is a finding, not a "
                            "pet project".format(iid))

    # Schedule: start no earlier than the wave start and no earlier than every predecessor's end.
    scheduled = {}

    def schedule(iid, stack):
        if iid in scheduled:
            return scheduled[iid]
        if iid in stack:
            warnings.append("circular dependency involving {} - scheduled at its wave start".format(iid))
            ini = inits[iid]
            scheduled[iid] = (WAVE_START_MONTH.get(ini["wave"], 0),
                              WAVE_START_MONTH.get(ini["wave"], 0) + ini["duration_months"])
            return scheduled[iid]
        stack.add(iid)
        ini = inits[iid]
        start = WAVE_START_MONTH.get(ini["wave"], 0)
        for dep in ini["depends_on"]:
            if dep in inits:
                start = max(start, schedule(dep, stack)[1])
        stack.discard(iid)
        scheduled[iid] = (start, start + ini["duration_months"])
        return scheduled[iid]

    for iid in order:
        schedule(iid, set())

    horizon = args.years * 12
    monthly_benefit = [0.0] * (horizon + 1)
    monthly_cost = [0.0] * (horizon + 1)

    for iid in order:
        ini = inits[iid]
        start, end = scheduled[iid]
        ini["start_month"], ini["end_month"] = start, end
        build_months = max(1, end - start)
        for m in range(1, horizon + 1):
            if start < m <= end:
                monthly_cost[m] += ini["cost_onetime"] / build_months
            if m > end:
                monthly_cost[m] += ini["cost_run_annual"] / 12.0
                monthly_benefit[m] += (ini["benefit_annual"] / 12.0
                                       * ramp_pct(m - end) * args.realisation)

    years = []
    cumulative = 0.0
    payback_month = None
    running = 0.0
    for m in range(1, horizon + 1):
        running += monthly_benefit[m] - monthly_cost[m]
        if payback_month is None and running >= 0 and m > 1:
            payback_month = m
    for y in range(args.years):
        lo, hi = y * 12 + 1, (y + 1) * 12
        ben = sum(monthly_benefit[lo:hi + 1])
        cost = sum(monthly_cost[lo:hi + 1])
        cumulative += ben - cost
        years.append({"year": y + 1, "benefit": ben, "cost": cost, "net": ben - cost,
                      "cumulative": cumulative})

    # End-of-period discounting, matching Excel's NPV(rate, values) so the workbook and this
    # output agree to the last digit.
    npv = sum(y["net"] / ((1 + args.discount_rate) ** y["year"]) for y in years)

    by_category = {}
    for ini in inits.values():
        cat = ini["benefit_category"] or "unclassified"
        by_category[cat] = by_category.get(cat, 0.0) + ini["benefit_annual"]

    by_type = {}
    for ini in inits.values():
        by_type[ini["type"] or "unclassified"] = by_type.get(ini["type"] or "unclassified", 0) + 1

    def quadrant(ini):
        high_impact = ini["impact"] * 1 >= 4
        low_effort = ini["effort"] <= 2
        if high_impact and low_effort:
            return "Do now"
        if high_impact:
            return "Plan properly"
        if low_effort:
            return "Batch"
        return "Park"

    lines = ["# Transformation roadmap and business case", "",
             "Realisation factor **{:.0%}** applied to all benefits. Discount rate **{:.1%}**. "
             "Horizon **{} years**. Ramp: 0% months 0-3, 25% months 4-6, 60% months 7-12, "
             "100% thereafter.".format(args.realisation, args.discount_rate, args.years),
             "", "## Sequenced initiatives", "",
             "| ID | Initiative | Type | Wave | Start (mo) | Go-live (mo) | Owner | Quadrant | "
             "Benefit p.a. | Category | One-time cost |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for iid in sorted(order, key=lambda i: (inits[i]["start_month"], i)):
        ini = inits[iid]
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            ini["id"], ini["name"], ini["type"], ini["wave"], ini["start_month"], ini["end_month"],
            ini["owner"], quadrant(ini), money(ini["benefit_annual"]), ini["benefit_category"],
            money(ini["cost_onetime"])))

    lines += ["", "## Benefit by category - never blended into one headline", "",
              "| Category | Steady-state annual (gross) |", "|---|---|"]
    for cat in BENEFIT_CATEGORIES + [c for c in by_category if c not in BENEFIT_CATEGORIES]:
        if cat in by_category:
            lines.append("| {} | {} |".format(cat, money(by_category[cat])))
    lines += ["",
              "> Headline number = **hard / cash P&L only** (${}). Cost avoidance, working "
              "capital, productivity and risk appear as separate labelled lines "
              "(roadmap-and-business-case.md 2).".format(money(by_category.get("hard", 0.0))),
              "",
              "> Working capital benefit is a **one-time cash release** plus carry at the cost of "
              "capital - it is shown here at annual scale only because the source data is annual. "
              "Convert it before it reaches a P&L page."]

    lines += ["", "## Cash flow", "",
              "| Year | Benefit (ramped) | Cost | Net | Cumulative |", "|---|---|---|---|---|"]
    for y in years:
        lines.append("| {} | {} | {} | {} | {} |".format(
            y["year"], money(y["benefit"]), money(y["cost"]), money(y["net"]),
            money(y["cumulative"])))

    lines += ["",
              "- **NPV** at {:.1%}: **${}**".format(args.discount_rate, money(npv)),
              "- **Payback**: {}".format(
                  "month {}".format(payback_month) if payback_month
                  else "not achieved within the {}-year horizon".format(args.years)),
              "- **Total investment** (one-time): ${}".format(
                  money(sum(i["cost_onetime"] for i in inits.values()))),
              "- **Initiative mix**: " + ", ".join("{} {}".format(v, k) for k, v in sorted(by_type.items())),
              ""]
    if by_type.get("Stop", 0) == 0:
        lines.append("> No **Stop** initiatives. A roadmap with nothing to stop has not looked "
                     "hard - Stop items are the cheapest benefit available.")

    lines += ["", "## Sensitivity", "", "| Scenario | NPV |", "|---|---|"]
    for label, ben_mult, cost_mult in [("Base", 1.0, 1.0), ("Benefits -30%", 0.7, 1.0),
                                       ("Costs +20%", 1.0, 1.2), ("Both", 0.7, 1.2)]:
        scenario_npv = sum((y["benefit"] * ben_mult - y["cost"] * cost_mult)
                           / ((1 + args.discount_rate) ** y["year"]) for y in years)
        lines.append("| {} | ${} |".format(label, money(scenario_npv)))

    if warnings:
        lines += ["", "## Warnings", ""] + ["- " + w for w in warnings]

    payload = {"initiatives": [dict(inits[i], quadrant=quadrant(inits[i])) for i in order],
               "years": years, "npv": npv, "discount_rate": args.discount_rate,
               "realisation": args.realisation, "payback_month": payback_month,
               "benefit_by_category": by_category, "initiative_mix": by_type,
               "total_investment": sum(i["cost_onetime"] for i in inits.values()),
               "warnings": warnings}
    write_outputs(args.outdir, "roadmap", "\n".join(lines), payload)


# ---------------------------------------------------------------- cli

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--outdir", default="ft_output", help="directory for .md and .json output")
    sub = parser.add_subparsers(dest="command", parser_class=argparse.ArgumentParser)

    p_gap = sub.add_parser("gap", parents=[common], help="benchmark gap and value at stake")
    p_gap.add_argument("metrics")
    p_gap.add_argument("--benchmarks", default=DEFAULT_BENCHMARKS)
    p_gap.add_argument("--industry", default="cross-industry")
    p_gap.add_argument("--realisation", type=float, default=0.7)
    p_gap.set_defaults(func=run_gap)

    p_score = sub.add_parser("score", parents=[common], help="capability maturity heatmap")
    p_score.add_argument("assessment")
    p_score.set_defaults(func=run_score)

    p_road = sub.add_parser("roadmap", parents=[common], help="wave plan and business case")
    p_road.add_argument("initiatives")
    p_road.add_argument("--discount-rate", type=float, default=0.10)
    p_road.add_argument("--years", type=int, default=5)
    p_road.add_argument("--realisation", type=float, default=0.7)
    p_road.set_defaults(func=run_roadmap)

    p_all = sub.add_parser("all", parents=[common],
                           help="run all three against a template/asset directory")
    p_all.add_argument("--assets", default=os.path.join(HERE, "..", "assets"))
    p_all.add_argument("--industry", default="cross-industry")
    p_all.add_argument("--realisation", type=float, default=0.7)
    p_all.add_argument("--discount-rate", type=float, default=0.10)
    p_all.add_argument("--years", type=int, default=5)
    p_all.set_defaults(func=run_all)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    args.func(args)
    return 0


def run_all(args):
    class Ns:
        pass

    gap_args = Ns()
    gap_args.metrics = os.path.join(args.assets, "client-metrics-template.csv")
    gap_args.benchmarks = os.path.join(args.assets, "benchmarks.csv")
    gap_args.industry = args.industry
    gap_args.realisation = args.realisation
    gap_args.outdir = args.outdir
    run_gap(gap_args)

    score_args = Ns()
    score_args.assessment = os.path.join(args.assets, "capability-assessment-template.csv")
    score_args.outdir = args.outdir
    run_score(score_args)

    road_args = Ns()
    road_args.initiatives = os.path.join(args.assets, "initiative-backlog-template.csv")
    road_args.discount_rate = args.discount_rate
    road_args.years = args.years
    road_args.realisation = args.realisation
    road_args.outdir = args.outdir
    run_roadmap(road_args)


if __name__ == "__main__":
    sys.exit(main())
