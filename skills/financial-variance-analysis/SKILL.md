---
name: financial-variance-analysis
description: Decompose any financial variance into quantified drivers with a reconciled waterfall bridge and leadership-ready narratives. Use this skill whenever the user asks to analyze budget vs actual, year-over-year or period-over-period changes, do a variance analysis, explain why a P&L line moved, build a revenue or profit bridge, or prepare variance commentary — for their own company's numbers or a public company's reported results (e.g. "variance analysis for IBM", "why did margin drop", "bridge FY25 to FY24"). Pair with annual-report-analyzer when the inputs come from a public annual report.
---

# Financial Variance Analysis

Decompose a variance, verify it reconciles, visualize it as a waterfall, and explain it in language a CFO can forward. This skill assists with analysis workflows and is not financial advice; outputs should be reviewed by a qualified professional before formal reporting.

## Workflow

1. **Establish the comparison.** Actual vs budget, vs forecast, vs prior period, or vs prior year. If ambiguous, prior year is the default for public-company data.
2. **Compute the total variance** for each headline line (revenue, gross profit, operating/pre-tax income, net income) in both $ and %.
3. **Decompose** using the technique that fits (below). Every bridge must satisfy: start + sum(drivers) = end, exactly. If it doesn't, find the residual — never hide it in the largest driver.
4. **Separate operating performance from noise.** Explicitly isolate: one-time items (settlements, impairments, restructuring charges), lapped prior-year items (gains, charges that didn't recur), FX (reported vs constant-currency gap), and inorganic contribution (acquisitions). State what % of the favorable variance is genuinely operational.
5. **Render a waterfall** (chart if the environment supports it, otherwise the text format below) plus a reconciliation table.
6. **Write a narrative per material driver** using the template below, and close with a one-line leadership summary.

## Decomposition techniques

**Price / Volume:** Volume effect = ΔVolume × prior Price; Price effect = ΔPrice × actual Volume. Verify they sum to total.

**Segment contribution:** For multi-segment companies, each segment's revenue/profit delta is a driver; residual "Other/eliminations" is its own bar, never omitted.

**Rate / Mix (margins):** Rate effect = Σ actual volumeᵢ × Δrateᵢ; Mix effect = Σ prior rateᵢ × (actual mix − prior mix) shift. Use when blended margin moves but segment margins tell a different story.

**Expense category:** Split OpEx variance into headcount-driven, volume-driven, discretionary, contractual/fixed, one-time, and timing.

**FX split:** FX driver ≈ prior revenue × (reported growth % − constant-currency growth %). Label it separately; never blend into operational drivers.

## Materiality and prioritization

Investigate and narrate any driver exceeding ~10% of the total variance or ~0.5–1% of revenue. Prioritize by: absolute $ impact → unexpected direction → new vs trending. Aggregate the remainder into one "Other" bar (max 5–8 bars per waterfall).

## Text waterfall format

```
WATERFALL: Pre-tax income — FY25 vs FY24 ($M)
FY24                                      5,797
  [+] Gross profit growth                +3,746
  [+] Lapping prior-year pension charge  +3,392
  [-] Prior-year divestiture gains & FX  -1,079
  [-] R&D investment                       -837
  [-] SG&A                                 -435
  [-] Interest expense                     -223
  [-] Other                                 -33
FY25                                     10,328   (+4,531, +78.2%)
```

Follow with a table: Driver | Amount | % of variance. Percentages may exceed 100% when drivers offset — note it.

## Narrative template (per driver)

```
[Line item]: [Favorable/Unfavorable] $[X] ([Y]%) vs [basis]
Driver: [named cause — specific, quantified, causal, 2–3 sentences]
Outlook: [one-time / recurring / cyclical / improving / deteriorating]
Action: [none / monitor / investigate / update forecast]
```

Anti-patterns to reject: circular explanations ("revenue was higher due to higher revenue"), "timing" without what and when it normalizes, "one-time" without naming the item, "various small items" for a material driver.

## Leadership summary (always include)

One sentence stating what the comparable, noise-adjusted performance actually was — e.g. "GAAP profit +78% overstates the story; on a comparable basis revenue grew 6% CC and operating pre-tax income 13%, with one-time laps accounting for most of the GAAP optics."

## Hand-offs

- Inputs from a public annual report or 10-K → run `annual-report-analyzer` first.
- Deliverable as Excel bridge with formulas → `xlsx` skill.
- Deliverable as branded slide → `ibm-branded-pptx` / `file-to-pptx`.
- Two-company comparison → `earnings-peer-comparison`.
