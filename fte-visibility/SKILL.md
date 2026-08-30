---
name: fte-visibility
description: Conduct the FTE Effort & Cost-Center Visibility workflow — join headcount, cost-center, and allocation extracts into the monthly effort model, surface the unallocated-FTE number, and draft the reviewed monthly narrative. Use when the user mentions FTE tracking, effort visibility, cost centers, capacity/utilization, "how many people are on X", or watsonx Challenge proposal 04.
---

# FTE Visibility — conduct guide

You (Bob) are conducting a monthly effort-visibility model. Privacy rule that overrides everything: **work at cost-center aggregates; never surface an individual employee's identity or allocation.**

## Step 1 — Run the model

Sample data: `python scripts/make_sample_data.py`. Then:
```
python scripts/fte_model.py --headcount hc.csv --costcenters cc.csv --alloc alloc.csv
```
Outputs to `model_out/`: `effort_by_target.csv`, `unallocated_fte.csv`, `cost_per_fte.csv`. Report the headline immediately: **total unallocated FTE** — that is the number the client has never seen. Distinguish its two causes when discussing: untracked work (fix allocation data) vs. misdeployed capacity (reallocate). Both are findings, not errors.

## Step 2 — Answer effort questions

MCP server `fte-visibility` if registered; otherwise call the functions in `scripts/fte_model.py` via shell:
`effort_by_process(top)` · `unallocated_fte()` · `cost_per_fte(cost_center)`
Answer only from the model output. "How many FTEs on month-end close?" → read it from `effort_by_process`, never estimate.

## Step 3 — Monthly narrative (drafted by agent, reviewed by human)

With `ICA_API_KEY`: `python scripts/fte_model.py ... --narrate` calls the ICA analyst agent.
Without it (Tier A): the same command writes `model_out/narrative_prompt.txt` — run that prompt yourself. Either way the narrative must contain: effort deltas vs. last month, the unallocated picture with the total stated plainly, three reallocation recommendations citing cost-per-FTE, and data-quality flags instead of guesses. **Label it DRAFT — a consultant reviews before the client sees it.**

## Step 4 — Client pack

On request, render the reviewed narrative + tables into the practice's branded deck format (same rules as Boblueprint Step 4: nothing invented; gaps become [SENIOR REVIEW] markers).

## Metric to capture
Model runtime (minutes) vs. the client's manual census baseline (weeks, quarterly); and the unallocated-FTE number itself, per month, in `runlog.md`. Full context: `references/proposal.md`; demo flow: `references/video-script.md`.
