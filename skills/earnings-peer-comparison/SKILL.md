---
name: earnings-peer-comparison
description: Compare two or more companies' reported financial results side by side on a like-for-like basis — growth, margins, cash generation, bookings/backlog, and segment dynamics. Use this skill whenever the user asks to compare, benchmark, or contrast companies' earnings, annual reports, or financial performance (e.g. "IBM vs Accenture", "how does our growth compare to peers", "benchmark these consulting firms"), or asks which company performed better in a period. Also use it after annual-report-analyzer has digested multiple reports and the user wants them bridged.
---

# Earnings Peer Comparison

Build a defensible side-by-side of two or more companies' reported results. The hard part is not the table — it's making the comparison honest.

## Workflow

1. **Gather primary sources.** Run `annual-report-analyzer` per company if digests aren't already in context. Never benchmark from news aggregators.
2. **Align the basis before comparing anything.** Work through the comparability checklist below and disclose every mismatch in the output.
3. **Build the comparison table** on the shared metric set (below), same fiscal labels, same currency, GAAP and adjusted shown separately.
4. **Narrate the deltas** — 3–5 insights explaining *why* the numbers diverge (business-model, mix, cycle position), not just that they do.
5. **State the caveats** in a closing note: any period misalignment, definitional differences, or one-time distortions that survive the adjustment.

## Comparability checklist (do not skip)

- **Fiscal calendars:** "FY2025" can mean different periods (IBM: ends Dec 31, 2025; Accenture: ends Aug 31, 2025 — eight months apart). Label every column with the actual period end date. If misalignment is material to the question, say so; optionally compare trailing-twelve-month figures instead.
- **GAAP vs adjusted:** compare GAAP to GAAP and adjusted to adjusted, never across. Name each company's adjustment basis (e.g. IBM "operating non-GAAP" excludes acquisition amortization and retirement items; Accenture "adjusted" excludes business optimization costs only — these are not equivalent).
- **One-time items:** flag anything distorting either side (pension settlements, restructuring charges, divestiture gains, tax-audit benefits) and show the noise-adjusted comparison.
- **Segment recasts:** both companies may have reclassified segments/geographies mid-year (e.g. LatAm moving between regions). Compare only on the recast basis.
- **Currency:** prefer each company's constant-currency growth for like-for-like growth comparison; note reporting-currency differences.
- **Metric definitions:** "bookings", "signings", "backlog", "ARR", "book-to-bill" are company-defined, not standardized. Compare directionally and footnote the definitions.

## Shared metric set

Revenue and growth (reported + constant currency) · gross margin · operating margin (GAAP + adjusted) · net income and EPS (GAAP + adjusted) · free cash flow and FCF margin · cash returned to shareholders (dividends + buybacks) · bookings or signings and book-to-bill where applicable · headcount if disclosed · forward guidance. Add domain metrics when both sides report them (AI bookings/book of business, ARR, backlog).

## Output format

Lead with a one-paragraph verdict answering the user's actual question. Then the comparison table. Then the insight narratives. Then caveats. If the environment supports charts, a paired-bar or dumbbell chart of 3–4 headline metrics helps; otherwise the table suffices.

## Insight quality bar

Good: "Accenture Consulting grew 5% LC vs IBM Consulting's 0.4% CC, but the businesses differ — IBM's consulting is a pull-through channel for its software/infrastructure flywheel (>80% of revenue from multi-segment clients), while Accenture's is the core engine; IBM's growth came from Software (+9% CC) instead."
Bad: "Accenture grew faster than IBM in consulting." (true, explains nothing)

## Hand-offs

- Deliverable as Excel scorecard → `xlsx` skill.
- Branded comparison deck → `ibm-branded-pptx` / `file-to-pptx`.
- Driver-level bridge of one company's change → `financial-variance-analysis`.
