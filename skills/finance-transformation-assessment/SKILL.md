---
name: finance-transformation-assessment
description: Conduct an end-to-end Finance Transformation assessment — define the target operating model, benchmark the client against industry quartiles, diagnose pain points across the five lenses (people / policy / process / data / technology), quantify value at stake, and build the phased transformation roadmap and business case, then render the deliverables as a client-ready deck and Excel model in IBM Consulting house style. Use when the user mentions finance transformation, current-state/as-is assessment, target operating model, finance blueprint, capability or maturity assessment, benchmarking, pain point analysis, value at stake, transformation roadmap, business case, CFO agenda diagnostic, house style / banned marketing words in a finance deliverable, or the golden threads (RTR / Record-to-Report, OTC / Order-to-Cash, S2P / Source-to-Pay) and their AI use case modals.
---

# Finance Transformation Assessment — conduct guide

You are conducting a consulting-grade finance transformation assessment. It runs in five
phases and ends in three deliverables: **(1) Assessment Findings & Blueprint**,
**(2) Transformation Roadmap & Business Case**, **(3) the deck + Excel model** that carry them.

**Vocabulary — read first.** In this practice, **"blueprint" means the house use-case deliverable**
(narrative → 4 pain points → 3 agents → user benefits → 4 business benefits → checkpoint flags),
owned and enforced by the Blueprint Accelerator. The function-level architecture this skill's
Phase 1 produces is called the **target operating model (TOM)**. Never use "blueprint" for the TOM.
The full contract, the closed enums, the house voice rules and the two-taxonomy reconciliation are
in `references/house-style-and-blueprint-contract.md` — **read it before drafting any client-facing
content**, and defer to `H:\My Drive\AA\blueprint-accelerator` wherever the two disagree.

Four hard rules, applied at every phase:

1. **Every number traces to client data or a cited benchmark.** Never estimate a client
   metric. Missing data goes to the "Data requests / further analysis" list — visible in the
   deliverable, not silently interpolated.
2. **Separate observation from inference from recommendation.** A finding states what was
   observed and its evidence; the implication is labelled as inference; the recommendation is
   labelled as ours. Clients challenge blended claims and win.
3. **Benchmarks are context, not verdicts.** Always state the source, the population, the
   as-of date, and why the peer set is comparable — see `references/benchmark-library.md` §0
   for the citation discipline and the four ways benchmark comparisons go wrong.
4. **House style binds.** Active voice, present tense, third person, sentences averaging ~18
   words (hard cap 28). Lint before delivery: `python scripts/ft_house_style.py <path>`.
   No marketing words: <!-- house-style: allow -->
   *leverage, unlock, empower, seamless, robust, synergy, best-in-class, world-class,
   transformative*.

## Phase 1 — Frame and define the target operating model

Establish scope before analysis: which processes, which entities/regions, which systems, and what
"good" means for this client.

**Set scope in golden thread identifiers.** The practice's process spine is three threads —
**RTR** (Record-to-Report, 12 sections / 73 steps), **S2P** (Source-to-Pay, 16 / 59) and **OTC**
(Order-to-Cash, 11 / 88), 220 steps in total, held in `assets/golden-thread-taxonomy.csv`:

```
python scripts/ft_golden_thread.py scope 1.7 1.8 1.9 3.7 3.9
```

That returns the step list, the mapping to the assessment taxonomy, the mapping to the closed
**process area enum**, and a checkpoint flag for any section with no enum member — scope that falls
outside is assessed normally but cannot be drafted as a blueprint later, which is a flag to raise
now rather than at Phase 5. `references/golden-threads.md` carries the framework, and browse with
`ft_golden_thread.py list --thread RTR --section 1.8`.

Then draft the **target operating model** — the seven layers (value proposition, service delivery
model, process architecture, data & technology, organization & talent, governance & policy,
performance management) at Level 2 detail. Work from `references/target-operating-model.md`, which
carries the process taxonomy, the delivery-model options with their trade-offs, and the maturity
model (5 levels × 5 lenses) you will score in Phase 3.

Fill the capability scope sheet from `assets/capability-assessment-template.csv`.

**Gate 1:** the client confirms scope, the peer set, and the target operating model's design
principles before any diagnostic work. Design principles chosen late invalidate the roadmap.

## Phase 2 — Benchmark the current state

Collect the client's actual metrics into `assets/client-metrics-template.csv`, then:

```
python scripts/ft_analyze.py gap assets/client-metrics-template.csv --industry cross-industry
```

This joins each metric to `references/benchmark-library.md`, computes the quartile position,
the gap to median and to top quartile, and the **value at stake** (gap × the driver volume you
supply). Read §0 of the library before quoting anything: every row carries a source, an as-of
date, and a confidence flag — `verified` rows may be quoted with the citation shown, `directional`
rows may only be used to frame a range, and you must never present a directional row as a number
on a client page.

Industry cuts available: cross-industry, distribution/transportation, consumer products,
retail/wholesale, financial services/banking, services, public sector, manufacturing, healthcare,
energy/utilities. Where an industry row is absent, say so and use cross-industry explicitly labelled.

## Phase 3 — Diagnose pain points across the five lenses

Run the diagnostic in `references/pain-point-taxonomy.md`: interview guide, the observation →
root cause → lens classification chain, and the severity × frequency × effort scoring. Every pain
point is assigned a **primary lens** (people / policy / process / data / technology) and a **root
cause**, not just a symptom. The lens distribution is itself a finding — a pain point set that is
90% "technology" almost always means the interviews stopped at the first answer.

Record a **pain dimension** on every row as well (`cycle_time`, `control_risk`, `data_quality`,
`decision_quality`, `scalability`) and the **golden thread `step`** the finding sits on, so
findings, benchmarks and modals all reconcile against one spine. The lens is where the cause sits;
the dimension is what it costs the business, and the blueprint contract requires at least three
distinct dimensions across the four pain points of any use case. Use personas from
`blueprint-accelerator/personas/inventory.yaml` — a persona not in the inventory raises a
`persona_flag` and never enters a deliverable unreviewed.

Score the capability maturity from your filled assessment sheet:

```
python scripts/ft_analyze.py score assets/capability-assessment-template.csv
```

Output is the maturity heatmap (capability × lens), the weighted score per capability, and the
gap to the target maturity you set in Phase 1.

**Gate 2:** walk the pain point register and the maturity heatmap through the process owners
before it reaches the CFO. Owners who first see their process rated in the steering deck become
opponents of the roadmap.

## Phase 4 — Build the roadmap and business case

Convert findings into initiatives in `assets/initiative-backlog-template.csv` (each traced to
the pain points it resolves), then sequence:

```
python scripts/ft_analyze.py roadmap assets/initiative-backlog-template.csv
```

This produces the impact/effort matrix, the dependency-respecting wave plan (Wave 1 quick wins
0–6 mo · Wave 2 core 6–18 mo · Wave 3 structural 18–36 mo), the benefit ramp, and the
cumulative net-benefit curve. `references/roadmap-and-business-case.md` carries the benefit
taxonomy (hard / soft / cost avoidance / working capital — never sum them into one headline),
the value driver tree, the ramp conventions, and the risk and change-impact treatment.

**Gate 3:** benefits must be owned. Any benefit line without a named accountable executive and
a baseline metric is presented as an *opportunity*, not a *benefit*.

### Hand off to the Blueprint Accelerator

Every initiative that introduces agents becomes a **use-case blueprint**. Name them here — an
assessment that ends without saying which blueprints to draft has stopped one step short. Add a
`golden_thread_steps` column to the backlog (semicolon-separated step ids, e.g. `3.7.3;3.9.4`),
then build the queue:

```
python scripts/ft_golden_thread.py queue <backlog.csv> --register <register.csv>
```

It orders by wave, resolves the process area from the thread steps, and reports which initiatives
have the four evidenced pain points the contract requires and which are blocked. Per draftable
initiative, hand `03-boblueprint-accelerator`: the `process_area`, the four pain points (highest
severity × frequency, then swapped for dimensional coverage until three dimensions appear), the
personas, and the SOW excerpt and interview notes.

Where the thread step already carries a prototype modal, you are **converting, not drafting** —
`references/golden-threads.md` §3 lists the two structural deltas (modals carry 3 pain points, the
contract needs 4; modals carry one user benefit per role, the contract needs 3). Close both from
the register. The accelerator enforces the counts: never pad to hit one, and never propose an agent
without a named human approver and a pause trigger.

## Phase 5 — Render the deliverables

Build the Excel model first — it is the evidence base the deck points to:

```
python scripts/ft_workbook.py --out FT_Assessment_Model.xlsx
```

Ten sheets: Executive Summary · Benchmark Gaps · Value at Stake · Maturity Heatmap · Pain Point
Register · Initiative Backlog · Roadmap (Gantt) · Business Case · Assumptions · Sources —
with native Excel charts (radar, bar-gap, waterfall-style benefit bridge, stacked wave plan) so
the client can re-cut the numbers without you.

Then the deck. Storyline patterns, the page-by-page skeleton, chart selection rules, and the
diagram conventions are in `references/deliverable-standards.md`. For rendering:
- **Deck:** use the `ibm-branded-pptx` skill for IBM-branded decks (or `pptx` for neutral). Pass
  it the storyline from `deliverable-standards.md` §2, not raw findings. For the accelerator's own
  10-slide pitch deck, the slot-by-slot spec already exists at
  `H:\My Drive\AA\blueprint-accelerator\slide-spec.md` — use it rather than rebuilding.
- **Process/swimlane diagrams:** use the `swimlane-diagram` skill for hand-off maps.
- **Chart styling:** follow the `dataviz` skill before writing any chart code.
- **Excel beyond the model:** the `xlsx` skill.

**Gate 4:** before the deck ships, run the completeness check in `deliverable-standards.md` §5
— every page traced to evidence, every benchmark cited, every `[SENIOR REVIEW]` marker resolved —
and lint the house style:

```
python scripts/ft_house_style.py <deck-text-or-directory>
```

Insert `[SENIOR REVIEW]` where the analysis lacks content; never invent a finding to fill a page.
Nothing SOX-relevant reaches a client without senior consultant sign-off.

## When only part of this is asked for

Each phase stands alone. "Benchmark us against the industry" is Phase 2 only; "build the
roadmap from these findings" is Phase 4 only. Run the phase asked for, and name the upstream
inputs you are assuming rather than silently inventing them.

For an RFP or proposal built on this assessment, use the `rfp-response` skill (09) — it consumes
the Phase 2 benchmarks and the Phase 4 roadmap directly. To draft the use-case blueprints
themselves, `boblueprint-accelerator` (03). For AR/O2C-specific depth use `ar-diagnostic` (06);
for the contract and TA that follow, `contract-review` (07).

## References
- `references/house-style-and-blueprint-contract.md` — **read first.** Blueprint vs target
  operating model, the enforced blueprint contract and counts, closed enums (process areas,
  archetypes, pain dimensions), house voice rules, checkpoint flags, the ~45% collision.
- `references/golden-threads.md` — the RTR / S2P / OTC thread spine (220 steps), the modal schema
  and its deltas from the blueprint contract, the three persona sets, the six-phase agentic app
  method with its GREEN/AMBER/RED autonomy zones, and which Studio source documents are
  prototype-faithful.
- `assets/golden-thread-taxonomy.csv` — every step with section, thread, process area and
  assessment mapping. Queried by `scripts/ft_golden_thread.py` (`list` / `scope` / `queue`).
- `references/target-operating-model.md` — the seven TOM layers, APQC-aligned finance process
  taxonomy, service delivery model options, the 5×5 maturity model, design principles.
- `references/benchmark-library.md` — cited benchmark tables with industry cuts, citation
  discipline, refresh procedure.
- `references/pain-point-taxonomy.md` — five-lens classification, interview guide, root-cause
  patterns, scoring.
- `references/roadmap-and-business-case.md` — wave planning, benefit taxonomy and ramps, value
  driver tree, risk/change treatment.
- `references/deliverable-standards.md` — deck storyline, chart and diagram selection, Excel
  model spec, quality checklist.
- `assets/process-flows.md` — ready-to-render P2P / O2C / R2R hand-off maps, blueprint layer
  diagram, current→target shift table and roadmap Gantt, with what to look for at each hand-off.
- `assets/*.csv` — the five input templates (benchmarks, client metrics, capability assessment,
  pain point register, initiative backlog), pre-filled with a worked example so every script runs
  out of the box. Replace the example rows with client data; keep the column headers.
