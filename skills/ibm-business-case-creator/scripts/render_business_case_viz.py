#!/usr/bin/env python3
"""Render HTML and PNG visualizations for a business case.

Input is a scenario-based JSON document with explicit `base_case`,
`best_case`, and `worst_case` economics.

This script intentionally avoids non-standard dependencies so it can run in the
repository's default environment.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

try:
    _pil = importlib.import_module("PIL")
    Image = importlib.import_module("PIL.Image")
    ImageDraw = importlib.import_module("PIL.ImageDraw")
    ImageFont = importlib.import_module("PIL.ImageFont")
except ImportError:
    Image = ImageDraw = ImageFont = None  # type: ignore[assignment]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a business case visualization HTML file.")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output HTML")
    parser.add_argument("--png-output", help="Optional path to output PNG")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def require_keys(obj: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise ValueError(f"{context} is missing required keys: {', '.join(missing)}")


def monthly_total(items: list[dict[str, Any]]) -> float:
    return float(sum(float(item.get("monthly_amount", 0)) for item in items))


def nonzero_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = [item for item in items if float(item.get("monthly_amount", 0)) > 0]
    if filtered:
        return filtered
    return items[:1]


def spread_implementation_cost(total_cost: float, duration: int, month_index: int) -> float:
    if duration <= 0 or month_index >= duration:
        return 0.0
    return total_cost / duration


def normalize_ramp(ramp: list[Any], timeline_months: int) -> list[float]:
    values = [float(v) for v in ramp]
    if not values:
        values = [1.0] * timeline_months
    if len(values) < timeline_months:
        values.extend([values[-1]] * (timeline_months - len(values)))
    return values[:timeline_months]


def validate_cost_items(items: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{context} must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{context}[{idx}] must be an object")
        require_keys(item, ["label", "monthly_amount"], f"{context}[{idx}]")
        normalized.append({"label": str(item["label"]), "monthly_amount": float(item["monthly_amount"])})
    return normalized


def validate_string_list(items: Any, context: str) -> list[str]:
    if not isinstance(items, list):
        raise ValueError(f"{context} must be a list")
    return [str(item) for item in items]


def validate_scenario(name: str, scenario: Any, timeline_months: int) -> dict[str, Any]:
    if not isinstance(scenario, dict):
        raise ValueError(f"scenarios.{name} must be an object")
    require_keys(
        scenario,
        [
            "implementation_duration_months",
            "implementation_cost",
            "monthly_benefit_ramp",
            "current_state_costs",
            "future_state_costs",
            "benefit_drivers",
        ],
        f"scenarios.{name}",
    )
    implementation_duration = int(scenario["implementation_duration_months"])
    if implementation_duration < 0:
        raise ValueError(f"scenarios.{name}.implementation_duration_months must be >= 0")
    ramp = normalize_ramp(scenario["monthly_benefit_ramp"], timeline_months)
    return {
        "implementation_duration_months": implementation_duration,
        "implementation_cost": float(scenario["implementation_cost"]),
        "monthly_benefit_ramp": ramp,
        "current_state_costs": validate_cost_items(scenario["current_state_costs"], f"scenarios.{name}.current_state_costs"),
        "future_state_costs": validate_cost_items(scenario["future_state_costs"], f"scenarios.{name}.future_state_costs"),
        "benefit_drivers": validate_cost_items(scenario["benefit_drivers"], f"scenarios.{name}.benefit_drivers"),
        "notes": validate_string_list(scenario.get("notes", []), f"scenarios.{name}.notes"),
    }


def validate_input_schema(data: dict[str, Any]) -> dict[str, Any]:
    require_keys(
        data,
        ["title", "subtitle", "currency_symbol", "currency_code", "timeline_months", "kpi_deltas", "assumptions", "scenarios"],
        "root",
    )
    timeline_months = int(data["timeline_months"])
    if timeline_months <= 0:
        raise ValueError("timeline_months must be > 0")
    scenarios = data["scenarios"]
    if not isinstance(scenarios, dict):
        raise ValueError("scenarios must be an object")
    required_scenarios = ["base_case", "best_case", "worst_case"]
    for name in required_scenarios:
        if name not in scenarios:
            raise ValueError(f"scenarios must include {', '.join(required_scenarios)}")

    validated = {
        "title": str(data["title"]),
        "subtitle": str(data["subtitle"]),
        "currency_symbol": str(data["currency_symbol"]),
        "currency_code": str(data["currency_code"]),
        "timeline_months": timeline_months,
        "kpi_deltas": data["kpi_deltas"],
        "assumptions": validate_string_list(data["assumptions"], "assumptions"),
        "scenarios": {name: validate_scenario(name, scenarios[name], timeline_months) for name in required_scenarios},
    }
    return validated


def calc_scenario(name: str, scenario: dict[str, Any], timeline_months: int) -> dict[str, Any]:
    implementation_duration = int(scenario.get("implementation_duration_months", 0))
    implementation_cost = float(scenario.get("implementation_cost", 0))
    current_cost = monthly_total(scenario.get("current_state_costs", []))
    future_cost = monthly_total(scenario.get("future_state_costs", []))
    run_rate_benefit = monthly_total(scenario.get("benefit_drivers", []))
    ramp = normalize_ramp(scenario.get("monthly_benefit_ramp", []), timeline_months)

    current_cumulative: list[float] = []
    future_cumulative: list[float] = []
    net_cash_flow: list[float] = []
    cumulative_net_benefit: list[float] = []

    current_total = 0.0
    future_total = 0.0
    cumulative_net = 0.0
    break_even_month: int | None = None

    for month_idx in range(timeline_months):
        current_total += current_cost
        implementation_spend = spread_implementation_cost(
            implementation_cost,
            implementation_duration,
            month_idx,
        )
        realized_benefit = run_rate_benefit * ramp[month_idx]
        month_future_cost = future_cost + implementation_spend

        future_total += month_future_cost
        month_net = realized_benefit - implementation_spend - future_cost + current_cost
        cumulative_net += month_net

        current_cumulative.append(round(current_total, 2))
        future_cumulative.append(round(future_total, 2))
        net_cash_flow.append(round(month_net, 2))
        cumulative_net_benefit.append(round(cumulative_net, 2))

        if break_even_month is None and cumulative_net >= 0:
            break_even_month = month_idx + 1

    annual_current = current_cost * 12
    annual_future = future_cost * 12
    annual_benefit = run_rate_benefit * 12
    annual_net_benefit = annual_benefit - (annual_future - annual_current)
    total_benefit = sum(run_rate_benefit * value for value in ramp)
    roi_percent = ((total_benefit - implementation_cost) / implementation_cost * 100) if implementation_cost else 0.0

    return {
        "timeline_months": timeline_months,
        "implementation_duration_months": implementation_duration,
        "implementation_cost": implementation_cost,
        "current_monthly_cost": current_cost,
        "future_monthly_cost": future_cost,
        "annual_current_cost": annual_current,
        "annual_future_cost": annual_future,
        "annual_benefit": annual_benefit,
        "annual_net_benefit": annual_net_benefit,
        "total_benefit": total_benefit,
        "roi_percent": roi_percent,
        "break_even_month": break_even_month,
        "current_cumulative": current_cumulative,
        "future_cumulative": future_cumulative,
        "net_cash_flow": net_cash_flow,
        "cumulative_net_benefit": cumulative_net_benefit,
        "label": name.replace("_", " ").title(),
    }


def calc_series(data: dict[str, Any]) -> dict[str, Any]:
    timeline_months = int(data.get("timeline_months", 36))
    scenarios = {
        name: calc_scenario(name, scenario, timeline_months)
        for name, scenario in data["scenarios"].items()
    }

    best = scenarios["best_case"]
    base = scenarios["base_case"]
    worst = scenarios["worst_case"]
    if not (best["roi_percent"] >= base["roi_percent"] >= worst["roi_percent"]):
        raise ValueError("Scenario ROI ordering is invalid: expected best_case >= base_case >= worst_case")

    comparable_break_evens = [s["break_even_month"] for s in (best, base, worst) if s["break_even_month"] is not None]
    if len(comparable_break_evens) == 3 and not (best["break_even_month"] <= base["break_even_month"] <= worst["break_even_month"]):
        raise ValueError("Scenario break-even ordering is invalid: expected best_case <= base_case <= worst_case")

    return {
        "timeline_months": timeline_months,
        "base_case": base,
        "best_case": best,
        "worst_case": worst,
        "scenario_order": ["best_case", "base_case", "worst_case"],
    }


def format_currency(amount: float, currency_symbol: str) -> str:
    rounded = round(amount)
    return f"{currency_symbol}{rounded:,.0f}"


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def build_html(data: dict[str, Any], computed: dict[str, Any]) -> str:
    title = html_escape(str(data.get("title", "Business Case Visualization")))
    subtitle = html_escape(str(data.get("subtitle", "")))
    currency_symbol = str(data.get("currency_symbol", "GBP"))
    assumptions = [html_escape(str(item)) for item in data.get("assumptions", [])]
    kpi_deltas = data.get("kpi_deltas", [])
    base_case = computed["base_case"]
    current_items = nonzero_items(data["scenarios"]["base_case"].get("current_state_costs", []))
    future_items = nonzero_items(data["scenarios"]["base_case"].get("future_state_costs", []))
    benefit_items = nonzero_items(data["scenarios"]["base_case"].get("benefit_drivers", []))

    cards = [
        (
            "Base-case break-even",
            f"Month {base_case['break_even_month']}" if base_case["break_even_month"] is not None else "Beyond horizon",
        ),
        ("Base-case annual net benefit", format_currency(base_case["annual_net_benefit"], currency_symbol)),
        ("Base-case ROI", f"{base_case['roi_percent']:.1f}%"),
        ("Worst-case ROI", f"{computed['worst_case']['roi_percent']:.1f}%"),
    ]
    cards_html = "\n".join(
        f"<div class='card'><div class='card-label'>{html_escape(label)}</div><div class='card-value'>{html_escape(value)}</div></div>"
        for label, value in cards
    )
    assumptions_html = "\n".join(f"<li>{item}</li>" for item in assumptions)
    kpi_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(str(item.get('label', '')))}</td>"
        f"<td>{html_escape(str(item.get('current', '')))}</td>"
        f"<td>{html_escape(str(item.get('future', '')))}</td>"
        f"<td>{html_escape(str(item.get('delta', '')))}</td>"
        "</tr>"
        for item in kpi_deltas
    )
    cost_profile_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(item['label'])}</td>"
        f"<td>{html_escape(format_currency(item['monthly_amount'], currency_symbol))}</td>"
        "</tr>"
        for item in current_items + future_items
    )
    scenario_cards = "\n".join(
        (
            "<div class='scenario-card'>"
            f"<div class='scenario-name'>{html_escape(computed[name]['label'])}</div>"
            f"<div class='scenario-stat'><span>Implementation</span><strong>{html_escape(format_currency(computed[name]['implementation_cost'], currency_symbol))}</strong></div>"
            f"<div class='scenario-stat'><span>Annual net benefit</span><strong>{html_escape(format_currency(computed[name]['annual_net_benefit'], currency_symbol))}</strong></div>"
            f"<div class='scenario-stat'><span>Break-even</span><strong>{html_escape(f'Month {computed[name]['break_even_month']}' if computed[name]['break_even_month'] is not None else 'Beyond horizon')}</strong></div>"
            f"<div class='scenario-stat'><span>ROI</span><strong>{html_escape(f'{computed[name]['roi_percent']:.1f}%')}</strong></div>"
            "</div>"
        )
        for name in ["best_case", "base_case", "worst_case"]
    )
    summary_note = html_escape(
        f"Base case breaks even in month {base_case['break_even_month']} with {base_case['roi_percent']:.1f}% ROI. "
        f"Worst case remains positive at {computed['worst_case']['roi_percent']:.1f}% ROI."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f2ede5;
      --panel: rgba(255, 252, 246, 0.92);
      --ink: #1b1b1b;
      --muted: #5a5a5a;
      --line: #d7cfc1;
      --blue: #0f62fe;
      --green: #198038;
      --purple: #8a3ffc;
      --red: #da1e28;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(15, 98, 254, 0.08), transparent 28%),
        linear-gradient(180deg, #f8f5ef 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 28px;
    }}
    .hero {{
      display: grid;
      gap: 10px;
      margin-bottom: 22px;
    }}
    .eyebrow {{
      display: inline-block;
      width: fit-content;
      padding: 7px 11px;
      border-radius: 999px;
      background: rgba(15, 98, 254, 0.08);
      color: var(--muted);
      font: 600 12px/1 Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    h1 {{
      margin: 0;
      font-size: 42px;
      line-height: 1.05;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 18px;
      max-width: 960px;
    }}
    .hero-note {{
      max-width: 960px;
      font: 500 20px/1.45 Georgia, "Times New Roman", serif;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 22px 0 28px;
    }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
    }}
    .card {{
      padding: 16px 18px;
      min-height: 112px;
      display: grid;
      gap: 8px;
    }}
    .card-label {{
      font: 600 12px/1 Arial, sans-serif;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .card-value {{
      font: 700 34px/1 Georgia, "Times New Roman", serif;
    }}
    .story-grid {{
      display: grid;
      grid-template-columns: 1.55fr 0.95fr;
      gap: 18px;
    }}
    .story-stack {{
      display: grid;
      gap: 18px;
    }}
    .bottom-grid {{
      display: grid;
      grid-template-columns: 0.95fr 1.2fr 1fr;
      gap: 18px;
      margin-top: 18px;
    }}
    .panel {{
      padding: 18px;
    }}
    .panel h2 {{
      margin: 0 0 12px;
      font-size: 24px;
    }}
    .panel p {{
      margin: 0 0 14px;
      color: var(--muted);
      font: 500 14px/1.5 Arial, sans-serif;
    }}
    .chart {{
      width: 100%;
      min-height: 340px;
    }}
    .chart text {{
      fill: var(--muted);
      font-size: 12px;
      font-family: Arial, sans-serif;
    }}
    .legend {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      font: 500 13px/1.4 Arial, sans-serif;
      color: var(--muted);
      margin-top: 10px;
    }}
    .swatch {{
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 999px;
      margin-right: 6px;
    }}
    .scenario-list {{
      display: grid;
      gap: 12px;
    }}
    .scenario-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: #fffdf8;
    }}
    .scenario-name {{
      margin-bottom: 8px;
      font: 700 12px/1 Arial, sans-serif;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .scenario-stat {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 0;
      border-top: 1px solid rgba(215, 207, 193, 0.8);
      font: 500 13px/1.4 Arial, sans-serif;
      color: var(--muted);
    }}
    .scenario-stat strong {{
      color: var(--ink);
      font-size: 16px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font: 500 13px/1.45 Arial, sans-serif;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font: 600 11px/1 Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    td:last-child, th:last-child {{
      text-align: right;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      overflow-wrap: anywhere;
    }}
    li {{
      margin-bottom: 10px;
      color: var(--muted);
      line-height: 1.45;
      font-family: Arial, sans-serif;
      font-size: 13px;
    }}
    @media (max-width: 1180px) {{
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .story-grid, .bottom-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 760px) {{
      .wrap {{ padding: 18px; }}
      .cards {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 32px; }}
      .hero-note {{ font-size: 18px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Business Case Snapshot</div>
      <h1>{title}</h1>
      <div class="subtitle">{subtitle}</div>
      <div class="hero-note">{summary_note}</div>
    </section>

    <section class="cards">
      {cards_html}
    </section>

    <section class="story-grid">
      <div class="panel">
        <h2>Cumulative Cost and Break-even</h2>
        <p>Base-case view of current-state cost, implementation spend, and cumulative net benefit over the full horizon.</p>
        <svg id="cumulative-chart" class="chart" viewBox="0 0 760 360" role="img" aria-label="Cumulative cost comparison chart"></svg>
        <div class="legend">
          <span><span class="swatch" style="background:#da1e28"></span>Current-state cumulative cost</span>
          <span><span class="swatch" style="background:#198038"></span>Future-state cumulative cost</span>
          <span><span class="swatch" style="background:#8a3ffc"></span>Cumulative net benefit</span>
        </div>
      </div>
      <div class="story-stack">
        <div class="panel">
          <h2>Scenario Comparison</h2>
          <p>Three explicit scenarios keep the model and the narrative aligned.</p>
          <div class="scenario-list">
            {scenario_cards}
          </div>
        </div>
        <div class="panel">
          <h2>KPI Snapshot</h2>
          <table>
            <thead>
              <tr>
                <th>KPI</th>
                <th>Current</th>
                <th>Future</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {kpi_rows}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="bottom-grid">
      <div class="panel">
        <h2>Base-case Cost Profile</h2>
        <table>
          <thead>
            <tr>
              <th>Cost line</th>
              <th>Monthly</th>
            </tr>
          </thead>
          <tbody>
            {cost_profile_rows}
          </tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Value Drivers</h2>
        <p>Only the quantified drivers carrying the financial case are shown.</p>
        <svg id="benefit-chart" class="chart" viewBox="0 0 560 340" role="img" aria-label="Benefit driver chart"></svg>
      </div>
      <div class="panel">
        <h2>Assumptions</h2>
        <ul>
          {assumptions_html}
        </ul>
      </div>
    </section>
  </div>
  <script>
    const payload = {dumps_json(data)};
    const computed = {dumps_json(computed)};

    function currency(amount) {{
      const symbol = payload.currency_symbol || "";
      return symbol + Number(amount).toLocaleString(undefined, {{ maximumFractionDigits: 0 }});
    }}

    function wrapText(value, maxChars) {{
      const words = String(value).split(/\\s+/);
      const lines = [];
      let current = "";
      for (const word of words) {{
        const candidate = current ? current + " " + word : word;
        if (candidate.length <= maxChars) {{
          current = candidate;
        }} else {{
          if (current) lines.push(current);
          current = word;
        }}
      }}
      if (current) lines.push(current);
      return lines;
    }}

    function createSvgLineChart(svgId, seriesList, breakEvenMonth, implementationDuration) {{
      const svg = document.getElementById(svgId);
      const width = 760;
      const height = 360;
      const margin = {{ top: 20, right: 20, bottom: 40, left: 70 }};
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const months = computed.timeline_months;
      const allValues = seriesList.flatMap(item => item.values);
      const maxY = Math.max(...allValues, 0) * 1.1 || 1;
      const x = (idx) => margin.left + (idx / Math.max(months - 1, 1)) * innerWidth;
      const y = (value) => margin.top + innerHeight - (value / maxY) * innerHeight;
      const ns = "http://www.w3.org/2000/svg";
      svg.innerHTML = "";

      const implRect = document.createElementNS(ns, "rect");
      implRect.setAttribute("x", x(0));
      implRect.setAttribute("y", margin.top);
      implRect.setAttribute("width", x(Math.max(implementationDuration - 1, 0)) - x(0));
      implRect.setAttribute("height", innerHeight);
      implRect.setAttribute("fill", "rgba(15, 98, 254, 0.08)");
      svg.appendChild(implRect);

      for (let i = 0; i < 5; i++) {{
        const guideValue = (maxY / 4) * i;
        const line = document.createElementNS(ns, "line");
        line.setAttribute("x1", margin.left);
        line.setAttribute("x2", width - margin.right);
        line.setAttribute("y1", y(guideValue));
        line.setAttribute("y2", y(guideValue));
        line.setAttribute("stroke", "#d9d3c7");
        line.setAttribute("stroke-width", "1");
        svg.appendChild(line);

        const label = document.createElementNS(ns, "text");
        label.setAttribute("x", 8);
        label.setAttribute("y", y(guideValue) + 4);
        label.textContent = currency(guideValue);
        svg.appendChild(label);
      }}

      for (let month = 0; month < months; month += Math.max(1, Math.floor(months / 6))) {{
        const label = document.createElementNS(ns, "text");
        label.setAttribute("x", x(month));
        label.setAttribute("y", height - 10);
        label.setAttribute("text-anchor", "middle");
        label.textContent = "M" + (month + 1);
        svg.appendChild(label);
      }}

      seriesList.forEach((series) => {{
        const path = document.createElementNS(ns, "path");
        const d = series.values.map((value, idx) => `${{idx === 0 ? "M" : "L"}} ${{x(idx)}} ${{y(value)}}`).join(" ");
        path.setAttribute("d", d);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", series.color);
        path.setAttribute("stroke-width", "3");
        svg.appendChild(path);
      }});

      if (breakEvenMonth) {{
        const breakX = x(breakEvenMonth - 1);
        const line = document.createElementNS(ns, "line");
        line.setAttribute("x1", breakX);
        line.setAttribute("x2", breakX);
        line.setAttribute("y1", margin.top);
        line.setAttribute("y2", margin.top + innerHeight);
        line.setAttribute("stroke", "#8a3ffc");
        line.setAttribute("stroke-dasharray", "6 6");
        line.setAttribute("stroke-width", "2");
        svg.appendChild(line);

        const label = document.createElementNS(ns, "text");
        label.setAttribute("x", breakX + 6);
        label.setAttribute("y", margin.top + 16);
        label.textContent = `Break-even: M${{breakEvenMonth}}`;
        svg.appendChild(label);
      }}
    }}

    function createBenefitChart(svgId, benefitItems) {{
      const svg = document.getElementById(svgId);
      const width = 560;
      const height = 340;
      const margin = {{ top: 20, right: 70, bottom: 20, left: 210 }};
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const maxValue = Math.max(...benefitItems.map(item => Number(item.monthly_amount || 0)), 1);
      const barGap = 18;
      const barHeight = (innerHeight - barGap * Math.max(benefitItems.length - 1, 0)) / Math.max(benefitItems.length, 1);
      const ns = "http://www.w3.org/2000/svg";
      svg.innerHTML = "";

      benefitItems.forEach((item, idx) => {{
        const amount = Number(item.monthly_amount || 0);
        const widthValue = (amount / maxValue) * innerWidth;
        const x = margin.left;
        const y = margin.top + idx * (barHeight + barGap);

        const rect = document.createElementNS(ns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", widthValue);
        rect.setAttribute("height", barHeight);
        rect.setAttribute("fill", "#198038");
        rect.setAttribute("rx", "8");
        svg.appendChild(rect);

        const valueLabel = document.createElementNS(ns, "text");
        valueLabel.setAttribute("x", x + widthValue + 8);
        valueLabel.setAttribute("y", y + barHeight / 2 + 4);
        valueLabel.textContent = currency(amount);
        svg.appendChild(valueLabel);

        wrapText(item.label, 26).forEach((lineText, lineIdx) => {{
          const label = document.createElementNS(ns, "text");
          label.setAttribute("x", 10);
          label.setAttribute("y", y + 16 + lineIdx * 13);
          label.textContent = lineText;
          svg.appendChild(label);
        }});
      }});
    }}

    createSvgLineChart(
      "cumulative-chart",
      [
        {{ values: computed.base_case.current_cumulative, color: "#da1e28" }},
        {{ values: computed.base_case.future_cumulative, color: "#198038" }},
        {{ values: computed.base_case.cumulative_net_benefit.map(value => Math.max(value, 0)), color: "#8a3ffc" }}
      ],
      computed.base_case.break_even_month,
      computed.base_case.implementation_duration_months
    );

    createBenefitChart("benefit-chart", {dumps_json(benefit_items)});
  </script>
</body>
</html>
"""


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
) -> tuple[int, int, int, int]:
    draw.text(xy, text, font=font, fill=fill)
    return draw.textbbox(xy, text, font=font)


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=2)


def wrap_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_line_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    series: list[tuple[list[float], str]],
    break_even_month: int | None,
    implementation_duration: int,
    currency_symbol: str,
) -> None:
    x0, y0, x1, y1 = box
    margin_left = 54
    margin_bottom = 30
    margin_top = 18
    inner_left = x0 + margin_left
    inner_top = y0 + margin_top
    inner_right = x1 - 16
    inner_bottom = y1 - margin_bottom
    width = max(inner_right - inner_left, 1)
    height = max(inner_bottom - inner_top, 1)
    months = max(len(series[0][0]), 1)
    max_value = max(max(values) for values, _ in series) if series else 1
    max_value = max(max_value, 1)
    axis_font = load_font(12)

    impl_end_x = inner_left + int(width * max(implementation_duration - 1, 0) / max(months - 1, 1))
    draw.rounded_rectangle((inner_left, inner_top, impl_end_x, inner_bottom), radius=10, fill="#e8f0ff")

    for idx in range(5):
        value = max_value * idx / 4
        y = inner_bottom - int(height * value / max_value)
        draw.line((inner_left, y, inner_right, y), fill="#d9d3c7", width=1)
        label = f"{currency_symbol}{value:,.0f}"
        draw.text((x0 + 4, y - 7), label, font=axis_font, fill="#5a5a5a")

    draw.line((inner_left, inner_top, inner_left, inner_bottom), fill="#8b8274", width=2)
    draw.line((inner_left, inner_bottom, inner_right, inner_bottom), fill="#8b8274", width=2)

    for month_idx in range(0, months, max(1, months // 6)):
        x = inner_left + int(width * month_idx / max(months - 1, 1))
        draw.text((x - 10, inner_bottom + 8), f"M{month_idx + 1}", font=axis_font, fill="#5a5a5a")

    for values, color in series:
        points: list[tuple[int, int]] = []
        for idx, value in enumerate(values):
            x = inner_left + int(width * idx / max(months - 1, 1))
            y = inner_bottom - int(height * value / max_value)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=color, width=4, joint="curve")

    if break_even_month is not None:
        x = inner_left + int(width * (break_even_month - 1) / max(months - 1, 1))
        draw.line((x, inner_top, x, inner_bottom), fill="#8a3ffc", width=3)
        draw.text((x + 6, inner_top), f"Break-even M{break_even_month}", font=axis_font, fill="#5a5a5a")


def draw_stacked_bars(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    current_items: list[dict[str, Any]],
    future_items: list[dict[str, Any]],
) -> None:
    x0, y0, x1, y1 = box
    inner_top = y0 + 18
    inner_bottom = y1 - 38
    height = max(inner_bottom - inner_top, 1)
    bar_width = 64
    left_x = x0 + 90
    right_x = x0 + 220
    palette = ["#0f62fe", "#198038", "#8a3ffc", "#ff832b", "#da1e28", "#525252"]
    axis_font = load_font(12)

    current_items = nonzero_items(current_items)
    future_items = nonzero_items(future_items)
    max_total = max(monthly_total(current_items), monthly_total(future_items), 1)

    def draw_bar(items: list[dict[str, Any]], base_x: int) -> None:
        offset = 0
        for idx, item in enumerate(items):
            amount = float(item.get("monthly_amount", 0))
            bar_h = int(height * amount / max_total)
            y = inner_bottom - offset - bar_h
            draw.rounded_rectangle((base_x, y, base_x + bar_width, y + bar_h), radius=10, fill=palette[idx % len(palette)])
            offset += bar_h

    draw_bar(current_items, left_x)
    draw_bar(future_items, right_x)
    draw.text((left_x + 8, inner_bottom + 10), "Current", font=axis_font, fill="#5a5a5a")
    draw.text((right_x + 14, inner_bottom + 10), "Future", font=axis_font, fill="#5a5a5a")

    legend_items = [*[{"side": "Current", **item} for item in current_items], *[{"side": "Future", **item} for item in future_items]][:5]
    for idx, item in enumerate(legend_items):
        y = y0 + 18 + idx * 28
        draw.rounded_rectangle((x0 + 10, y, x0 + 22, y + 12), radius=4, fill=palette[idx % len(palette)])
        label = f"{item['side']}: {item.get('label', '')}"
        for line_idx, line in enumerate(wrap_lines(draw, label, axis_font, 230)[:2]):
            draw.text((x0 + 30, y - 2 + line_idx * 12), line, font=axis_font, fill="#5a5a5a")


def draw_bar_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    items: list[dict[str, Any]],
    currency_symbol: str,
) -> None:
    x0, y0, x1, y1 = box
    items = nonzero_items(items)
    inner_left = x0 + 210
    inner_right = x1 - 70
    inner_top = y0 + 18
    inner_bottom = y1 - 24
    width = max(inner_right - inner_left, 1)
    height = max(inner_bottom - inner_top, 1)
    axis_font = load_font(12)
    max_value = max((float(item.get("monthly_amount", 0)) for item in items), default=1)
    max_value = max(max_value, 1)
    gap = 18
    bar_height = max((height - gap * max(len(items) - 1, 0)) // max(len(items), 1), 20)

    for idx, item in enumerate(items):
        amount = float(item.get("monthly_amount", 0))
        bar_w = int(width * amount / max_value)
        y = inner_top + idx * (bar_height + gap)
        draw.rounded_rectangle((inner_left, y, inner_left + bar_w, y + bar_height), radius=10, fill="#198038")
        draw.text((inner_left + bar_w + 8, y + 6), f"{currency_symbol}{amount:,.0f}", font=axis_font, fill="#5a5a5a")
        for line_idx, line in enumerate(wrap_lines(draw, str(item.get("label", "")), axis_font, 170)[:3]):
            draw.text((x0 + 12, y + 4 + line_idx * 12), line, font=axis_font, fill="#5a5a5a")


def draw_scenario_summary(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    computed: dict[str, Any],
    currency_symbol: str,
) -> None:
    x0, y0, x1, y1 = box
    header_font = load_font(12)
    value_font = load_font(16, bold=True)
    body_font = load_font(13)
    scenario_names = ["best_case", "base_case", "worst_case"]
    headers = ["Implementation", "Annual net benefit", "Break-even", "ROI"]
    col_width = (x1 - x0 - 24) // 3

    for idx, name in enumerate(scenario_names):
        left = x0 + 8 + idx * col_width
        right = left + col_width - 8
        draw.rounded_rectangle((left, y0 + 10, right, y1 - 10), radius=14, fill="#f7f2ea", outline="#d9d3c7", width=1)
        scenario = computed[name]
        draw.text((left + 12, y0 + 22), scenario["label"].upper(), font=header_font, fill="#5a5a5a")
        values = [
            format_currency(scenario["implementation_cost"], currency_symbol),
            format_currency(scenario["annual_net_benefit"], currency_symbol),
            f"Month {scenario['break_even_month']}" if scenario["break_even_month"] is not None else "Beyond horizon",
            f"{scenario['roi_percent']:.1f}%",
        ]
        row_y = y0 + 52
        for header, value in zip(headers, values):
            draw.text((left + 12, row_y), header, font=body_font, fill="#5a5a5a")
            draw.text((left + 12, row_y + 14), value, font=value_font, fill="#1b1b1b")
            row_y += 48


def draw_scenario_cards(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    computed: dict[str, Any],
    currency_symbol: str,
) -> None:
    x0, y0, x1, y1 = box
    label_font = load_font(12)
    value_font = load_font(22, bold=True)
    body_font = load_font(14)
    scenarios = [
        ("best_case", "#198038"),
        ("base_case", "#0f62fe"),
        ("worst_case", "#da1e28"),
    ]
    gap = 14
    card_height = (y1 - y0 - gap * (len(scenarios) - 1)) // len(scenarios)
    metrics = [
        ("Annual net benefit", lambda s: format_currency(s["annual_net_benefit"], currency_symbol)),
        ("Break-even", lambda s: f"Month {s['break_even_month']}" if s["break_even_month"] is not None else "Beyond horizon"),
        ("ROI", lambda s: f"{s['roi_percent']:.1f}%"),
    ]

    for idx, (name, accent) in enumerate(scenarios):
        top = y0 + idx * (card_height + gap)
        bottom = top + card_height
        draw.rounded_rectangle((x0, top, x1, bottom), radius=16, fill="#fffdf8", outline="#d9d3c7", width=1)
        draw.rounded_rectangle((x0 + 14, top + 16, x0 + 24, top + 30), radius=5, fill=accent)
        draw.text((x0 + 34, top + 14), computed[name]["label"].upper(), font=label_font, fill="#5a5a5a")
        scenario = computed[name]
        content_top = top + 46
        card_width = x1 - x0
        col_gap = 18
        col_width = (card_width - 36 - col_gap * 2) // 3
        for metric_idx, (metric_label, formatter) in enumerate(metrics):
            left = x0 + 18 + metric_idx * (col_width + col_gap)
            metric_y = content_top
            draw.text((left, metric_y), metric_label, font=body_font, fill="#5a5a5a")
            draw.text((left, metric_y + 14), formatter(scenario), font=value_font, fill="#1b1b1b")


def draw_named_amount_list(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    items: list[dict[str, Any]],
    currency_symbol: str,
    accent: str,
) -> None:
    x0, y0, x1, y1 = box
    title_font = load_font(20, bold=True)
    body_font = load_font(14)
    value_font = load_font(16, bold=True)
    draw_text(draw, (x0 + 18, y0 + 14), title, title_font, "#1b1b1b")
    y = y0 + 56
    for item in nonzero_items(items)[:4]:
        draw.rounded_rectangle((x0 + 18, y - 2, x0 + 30, y + 10), radius=4, fill=accent)
        for idx, line in enumerate(wrap_lines(draw, str(item.get("label", "")), body_font, x1 - x0 - 180)[:2]):
            draw.text((x0 + 40, y - 6 + idx * 14), line, font=body_font, fill="#5a5a5a")
        amount = format_currency(float(item.get("monthly_amount", 0)), currency_symbol)
        bbox = draw.textbbox((0, 0), amount, font=value_font)
        draw.text((x1 - 18 - (bbox[2] - bbox[0]), y - 6), amount, font=value_font, fill="#1b1b1b")
        y += 42


def draw_grouped_cost_profile(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    current_items: list[dict[str, Any]],
    future_items: list[dict[str, Any]],
    currency_symbol: str,
) -> None:
    x0, y0, x1, y1 = box
    title_font = load_font(22, bold=True)
    section_font = load_font(14, bold=True)
    body_font = load_font(13)
    value_font = load_font(14, bold=True)
    draw_text(draw, (x0 + 18, y0 + 14), "Cost Profile", title_font, "#1b1b1b")
    y = y0 + 54
    sections = [
        ("Current-state monthly cost", current_items, "#da1e28"),
        ("Future-state run cost", future_items, "#0f62fe"),
    ]
    for title, items, accent in sections:
        draw.rounded_rectangle((x0 + 18, y, x0 + 30, y + 12), radius=4, fill=accent)
        draw.text((x0 + 40, y - 2), title, font=section_font, fill="#1b1b1b")
        y += 28
        for item in nonzero_items(items)[:4]:
            label_lines = wrap_lines(draw, str(item.get("label", "")), body_font, x1 - x0 - 170)
            amount = format_currency(float(item.get("monthly_amount", 0)), currency_symbol)
            bbox = draw.textbbox((0, 0), amount, font=value_font)
            draw.text((x1 - 18 - (bbox[2] - bbox[0]), y), amount, font=value_font, fill="#1b1b1b")
            for idx, line in enumerate(label_lines[:2]):
                draw.text((x0 + 40, y + idx * 15), line, font=body_font, fill="#5a5a5a")
            y += 18 * min(len(label_lines), 2) + 10
        y += 10


def draw_kpi_list(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    kpi_deltas: list[dict[str, Any]],
) -> None:
    x0, y0, x1, y1 = box
    title_font = load_font(20, bold=True)
    body_font = load_font(14)
    delta_font = load_font(14, bold=True)
    draw_text(draw, (x0 + 18, y0 + 14), "KPI Snapshot", title_font, "#1b1b1b")
    y = y0 + 56
    for item in kpi_deltas[:5]:
        label = str(item.get("label", ""))
        detail = f"{item.get('current', '')} -> {item.get('future', '')}"
        delta = str(item.get("delta", ""))
        draw.text((x0 + 18, y), label, font=body_font, fill="#1b1b1b")
        draw.text((x0 + 18, y + 16), detail, font=body_font, fill="#5a5a5a")
        bbox = draw.textbbox((0, 0), delta, font=delta_font)
        draw.text((x1 - 18 - (bbox[2] - bbox[0]), y + 8), delta, font=delta_font, fill="#0f62fe")
        y += 44


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    items: list[str],
) -> None:
    x0, y0, x1, y1 = box
    title_font = load_font(20, bold=True)
    body_font = load_font(13)
    draw_text(draw, (x0 + 18, y0 + 14), title, title_font, "#1b1b1b")
    y = y0 + 56
    for item in items[:4]:
        wrapped = wrap_lines(draw, item, body_font, x1 - x0 - 48)
        draw.rounded_rectangle((x0 + 18, y + 4, x0 + 26, y + 12), radius=4, fill="#8a3ffc")
        for idx, line in enumerate(wrapped[:3]):
            draw.text((x0 + 34, y + idx * 16), line, font=body_font, fill="#5a5a5a")
        y += 18 * len(wrapped[:3]) + 10


def draw_kpi_assumptions_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    kpi_deltas: list[dict[str, Any]],
    assumptions: list[str],
) -> None:
    x0, y0, x1, y1 = box
    divider_x = x0 + (x1 - x0) // 2
    draw_kpi_list(draw, (x0, y0, divider_x - 10, y1), kpi_deltas[:3])
    draw.line((divider_x, y0 + 18, divider_x, y1 - 18), fill="#d9d3c7", width=1)
    draw_bullets(draw, (divider_x + 10, y0, x1, y1), "Assumptions", assumptions[:3])


def render_png(data: dict[str, Any], computed: dict[str, Any], output_path: Path) -> None:
    width = 1600
    height = 960
    image = Image.new("RGB", (width, height), "#f4efe6")
    draw = ImageDraw.Draw(image)

    title_font = load_font(40, bold=True)
    subtitle_font = load_font(18)
    card_value_font = load_font(28, bold=True)
    card_label_font = load_font(13)
    section_font = load_font(22, bold=True)
    body_font = load_font(15)
    small_font = load_font(13)

    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=28, fill="#faf7f1", outline="#d9d3c7", width=2)
    draw_text(draw, (56, 48), str(data.get("title", "Business Case Visualization")), title_font, "#1b1b1b")
    draw_text(draw, (58, 96), str(data.get("subtitle", "")), subtitle_font, "#5a5a5a")

    currency_symbol = str(data.get("currency_symbol", "GBP"))
    base_case = computed["base_case"]
    cards = [
        ("Current annual cost", format_currency(base_case["annual_current_cost"], currency_symbol)),
        ("Implementation cost", format_currency(base_case["implementation_cost"], currency_symbol)),
        ("Annual net benefit", format_currency(base_case["annual_net_benefit"], currency_symbol)),
        ("Base-case break-even", f"Month {base_case['break_even_month']}" if base_case["break_even_month"] is not None else "Beyond horizon"),
        ("Base-case ROI", f"{base_case['roi_percent']:.1f}%"),
    ]

    card_top = 138
    card_w = 286
    card_h = 96
    for idx, (label, value) in enumerate(cards):
        left = 56 + idx * (card_w + 12)
        draw_panel(draw, (left, card_top, left + card_w, card_top + card_h), "#fffaf2", "#d9d3c7")
        draw_text(draw, (left + 14, card_top + 16), label.upper(), card_label_font, "#5a5a5a")
        draw_text(draw, (left + 14, card_top + 48), value, card_value_font, "#1b1b1b")

    chart_panel = (56, 258, 980, 650)
    scenario_panel = (1004, 258, 1544, 650)
    cost_panel = (56, 674, 470, 916)
    value_panel = (494, 674, 908, 916)
    detail_panel = (932, 674, 1544, 916)

    for panel in (chart_panel, scenario_panel, cost_panel, value_panel, detail_panel):
        draw_panel(draw, panel, "#fffaf2", "#d9d3c7")

    draw_text(draw, (chart_panel[0] + 18, chart_panel[1] + 14), "Cumulative Cost and Break-even", section_font, "#1b1b1b")
    draw_text(
        draw,
        (chart_panel[0] + 18, chart_panel[1] + 46),
        "Base-case view of current-state cost, future-state cost, and cumulative net benefit across the modeled horizon.",
        body_font,
        "#5a5a5a",
    )
    draw_line_chart(
        draw,
        (chart_panel[0] + 10, chart_panel[1] + 78, chart_panel[2] - 10, chart_panel[3] - 50),
        [
            (base_case["current_cumulative"], "#da1e28"),
            (base_case["future_cumulative"], "#198038"),
            ([max(value, 0) for value in base_case["cumulative_net_benefit"]], "#8a3ffc"),
        ],
        base_case["break_even_month"],
        base_case["implementation_duration_months"],
        currency_symbol,
    )
    legend_items = [
        ("Current-state cumulative cost", "#da1e28"),
        ("Future-state cumulative cost", "#198038"),
        ("Cumulative net benefit", "#8a3ffc"),
    ]
    legend_y = chart_panel[3] - 28
    legend_x = chart_panel[0] + 22
    for label, color in legend_items:
        draw.rounded_rectangle((legend_x, legend_y + 2, legend_x + 12, legend_y + 14), radius=4, fill=color)
        draw.text((legend_x + 18, legend_y), label, font=small_font, fill="#5a5a5a")
        legend_x += 230

    draw_text(draw, (scenario_panel[0] + 18, scenario_panel[1] + 14), "Scenario Comparison", section_font, "#1b1b1b")
    scenario_intro = "Best, base, and worst cases are shown explicitly so the deck and the math do not contradict each other."
    for idx, line in enumerate(wrap_lines(draw, scenario_intro, body_font, scenario_panel[2] - scenario_panel[0] - 36)[:2]):
        draw_text(draw, (scenario_panel[0] + 18, scenario_panel[1] + 46 + idx * 18), line, body_font, "#5a5a5a")
    draw_scenario_cards(
        draw,
        (scenario_panel[0] + 18, scenario_panel[1] + 96, scenario_panel[2] - 18, scenario_panel[3] - 18),
        computed,
        currency_symbol,
    )

    draw_grouped_cost_profile(
        draw,
        cost_panel,
        data["scenarios"]["base_case"].get("current_state_costs", []),
        data["scenarios"]["base_case"].get("future_state_costs", []),
        currency_symbol,
    )

    draw_named_amount_list(
        draw,
        value_panel,
        "Value Drivers",
        data["scenarios"]["base_case"].get("benefit_drivers", []),
        currency_symbol,
        "#198038",
    )

    draw_kpi_assumptions_panel(draw, detail_panel, data.get("kpi_deltas", []), data.get("assumptions", []))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    data = validate_input_schema(load_json(input_path))
    computed = calc_series(data)
    html = build_html(data, computed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote visualization to {output_path}")
    if args.png_output:
        png_path = Path(args.png_output)
        render_png(data, computed, png_path)
        print(f"Wrote PNG visualization to {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
