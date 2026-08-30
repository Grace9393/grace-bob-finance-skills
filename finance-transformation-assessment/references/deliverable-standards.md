# Deliverable Standards — deck, workbook, charts, diagrams

The analysis is not the deliverable. What the client keeps is a deck and a workbook, and they are
judged on whether an executive can follow the argument in ten minutes and whether an analyst can
re-cut the numbers without you.

**House style binds every word here.** Active voice, present tense, third person. Sentences average
~18 words, hard cap 28. No marketing words, no filler hedges. The full rules and the rationale are
in `house-style-and-blueprint-contract.md` §5; the check is
`python scripts/ft_house_style.py <path>`, and it runs as part of the Gate in §5 below.

---

## 1. Rendering routes

| Deliverable | Route | Notes |
|---|---|---|
| IBM-branded deck | `ibm-branded-pptx` skill | Pass it the storyline from §2, not raw findings |
| Neutral deck | `pptx` skill | For client-template or white-label work |
| Excel model | `scripts/ft_workbook.py` (openpyxl, native charts) | Extend with the `xlsx` skill for bespoke sheets |
| Swimlane / hand-off maps | `swimlane-diagram` skill | Actors as lanes; hand-offs are the point |
| Any chart | Read the `dataviz` skill **before** writing chart code | Colour, axis, legend and accessibility rules |
| Architecture / target-state diagrams | `transformation-architecture-diagram` skill | Layered current → target views |
| The accelerator's own 10-slide pitch deck | `blueprint-accelerator/slide-spec.md` | Slot-by-slot spec with its own QA checklist — already written, do not rebuild |

Native Excel charts (not images) are mandatory in the workbook — the client re-cuts the data, and
a pasted picture makes the model dead on arrival.

---

## 2. Deck storyline

Executives read the horizontal — the sequence of page titles must tell the whole story on its own.
Test it: read only the titles aloud. If the argument does not hold, the deck does not either.

**Standard assessment readout (18–25 pages plus appendix):**

| # | Page | Content | Chart / visual |
|---|---|---|---|
| 1 | Title | Client, scope, date, version | — |
| 2 | Executive summary | The whole argument on one page: where you are, what it costs you, what to do, what it is worth | Four-box or KPI strip |
| 3 | Approach and evidence base | Interviews, data, systems, period covered. Establishes standing | Simple process bar + counts |
| 4 | Scope | Processes, entities, systems in and out | Taxonomy map with in-scope highlighted |
| 5–6 | Where you stand | Benchmark position on 4–6 headline metrics | Gap bars vs median and top quartile |
| 7 | Maturity | Capability × lens heatmap, current vs target | Heatmap + radar |
| 8–11 | What we found | One page per theme, not per pain point | Evidence callouts + quantum |
| 12 | Lens distribution | Where the problems really are | Stacked bar / donut by lens |
| 13 | Root causes | The 5–7 causes behind the themes | Cause → effect linkage |
| 14 | Value at stake | Gap sizing by driver, with realisation factor visible | Waterfall |
| 15 | Target blueprint | The seven layers, one page | Layered blueprint diagram |
| 16 | What changes | 6–10 headline shifts, from → to | Two-column from/to table |
| 17–18 | Roadmap | Three waves, initiatives, dependencies, owners | Gantt / wave chart |
| 19 | Business case | Investment, benefit by category, payback, NPV | Cumulative net benefit curve |
| 20 | Risks and what we need from you | Named risks, decisions required, dates | Risk table + decision log |
| 21 | Next steps | Who does what by when | Timeline |
| A | Appendix | Full registers, method, benchmark sources, data requests | Tables |

**Page construction rules:**
- **Action titles.** "DSO is 47 days against a 30-day top quartile, holding $18M of cash" — not
  "DSO analysis." A title stating the topic instead of the finding wastes the most-read line.
- One message per page. If a page needs two takeaways, it is two pages.
- Every number carries its source and as-of date on the page — benchmark citations per
  `benchmark-library.md` §0.
- Distinguish **observation / inference / recommendation** visually and consistently.
- `[SENIOR REVIEW]` wherever analysis is thin. Never invent content to fill a page; list every
  marker you inserted when you hand over.

**Alternative storylines:** *Board/CFO short form* (5 pages: situation → what it costs → what to
do → what it is worth → decisions needed). *Process-owner working session* (findings and register
in full, no executive framing). *Steering pack* (progress, decisions, risks, benefit tracking).

---

## 3. Chart selection

| Question the page answers | Chart | Avoid |
|---|---|---|
| How do we compare to peers? | Horizontal bar, client vs median vs top quartile, gap annotated | Gauge/speedometer — no precision, no context |
| Where does the value come from? | Waterfall (bridge) | Pie — cannot rank or sum accurately |
| How do capabilities score? | Heatmap (capability × lens), radar for current vs target overlay | Radar with >8 axes or >2 series |
| What happens when? | Gantt with dependency arrows | Undated milestone lists |
| When do we break even? | Cumulative net benefit line with zero crossing marked | Bar-only cash flow that hides the crossing |
| What is the composition? | Stacked bar (≤5 segments) | Stacked area with many series; 3-D anything |
| How are items distributed on two dimensions? | Impact/effort scatter with quadrant lines | Bubble charts with a third encoded dimension |
| How has it trended? | Line, with the target as a reference line | Dual axes — reliably misread |

Rules: sort bars by value, not alphabetically · label directly instead of using legends where
possible · start value axes at zero for bars · state the unit in the axis title · use one accent
colour for "client" against a neutral for benchmarks · never encode meaning in colour alone. Load
the `dataviz` skill for the full palette and accessibility treatment before writing chart code.

---

## 4. Excel workbook specification

`scripts/ft_workbook.py` builds this. Ten sheets, in this order:

| Sheet | Contents |
|---|---|
| `Executive Summary` | Headline metrics, value at stake, investment, payback — all formula-linked to other sheets, never hard-typed |
| `Benchmark Gaps` | Metric, client value, median, top quartile, gap, quartile position, source, as-of, confidence + gap bar chart |
| `Value at Stake` | Gap × driver volume × realisation factor, by metric, with the factor as an editable input cell |
| `Maturity Heatmap` | Capability × lens scores, current vs target, conditional formatting + radar chart |
| `Pain Point Register` | Full register with lens, root cause, scores, owner, initiative link |
| `Initiative Backlog` | All initiatives with type, benefit category, costs, effort/impact, dependencies, owner |
| `Roadmap` | Wave assignment, start/end months, Gantt bars, dependency flags |
| `Business Case` | Cost and benefit by year and category, net cash flow, cumulative curve, payback, NPV |
| `Assumptions` | Every assumption as a labelled input cell, referenced by formula elsewhere |
| `Sources` | Every benchmark citation with URL, as-of date, population, confidence flag |

Build rules:
- **Inputs are cells, not constants in formulas.** Realisation factor, discount rate, loaded cost
  per FTE and volumes all live on `Assumptions` and are referenced.
- Input cells styled distinctly from calculated cells; calculated cells are never hand-typed.
- Native charts only.
- Every sheet carries its as-of date and the source of the client data.
- No hidden rows or hidden sheets — a client who finds one stops trusting the model.

---

## 5. Quality gate — run before anything ships

0. **House style** — `python scripts/ft_house_style.py <path>` returns zero errors. Banned words
   and blueprint-contract violations block delivery; sentence-length warnings are advisory in
   internal documents and should be fixed in anything a client reads.
1. **Horizontal test** — page titles alone tell the argument.
2. **Traceability** — every number on every page traces to the workbook; every workbook figure
   traces to client data or a cited benchmark.
3. **Citation** — every benchmark shows source and as-of date; no `directional` row appears as a
   figure anywhere (`benchmark-library.md` §0).
4. **Arithmetic** — totals sum; benefit categories are not blended; no double counting across
   initiatives; workbook and deck agree to the last digit.
5. **Ownership** — every initiative and every benefit line has a named owner.
6. **Markers** — zero unresolved `[SENIOR REVIEW]`; all listed at handover.
7. **Register linkage** — every pain point maps to an initiative or is explicitly parked.
8. **Data gaps** — the "further analysis / data requests" list is present and honest.
9. **Client language** — the client's own process and system names, not the reference model's.
10. **Confidentiality** — no attributed interview quotes; findings aggregated as promised.
