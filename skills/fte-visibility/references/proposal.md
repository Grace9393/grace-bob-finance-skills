# Proposal 4 — FTE Effort & Cost-Center Visibility (Monica)

**2026 IBMer watsonx Challenge — business proposal + technique**

---

## Business proposal

**Executive summary.** Clients know *what* has to be done; they don't know *how many people they actually have on it*. At [CLIENT] and peers, effort is invisible: headcount lives in HR, cost in cost centers, work in projects and processes — never joined. We build a monthly pipeline that joins them, makes the **unallocated-FTE number** visible for the first time, and has an ICA agent narrate where effort went, what changed, and what to reallocate — with the evidence attached.

**Client pain & evidence.** Direct from the current [CLIENT] engagement: "they know what they need to do, but they don't know how many people they have and can't track it day to day." Every transformation baseline needs this and builds it manually, once, and it's stale in a month.

**Value.**
- The invisibility number: unallocated FTE by cost center, monthly, automatic (today: a quarterly manual census, if at all).
- Effort-vs-plan by process and project, with cost-per-FTE context.
- Reallocation recommendations a transformation lead can act on, cited to the model.

**Commercial angle.** Every operating-model and transformation engagement needs this baseline — it becomes a monthly-refresh asset we leave running (recurring value, not a one-time study). [INTERNAL]: run on the sanitized [CLIENT] structure we already work with.

**2026 fit.** Recurring monthly usage by design; human reviews the narrative before it reaches the client; Bob + ICA + client extracts only.

---

## Technique

### What Bob does
1. **Builds the model**: `fte_model.py` (join + allocation math + flags) written and iterated by Bob during the challenge.
2. **Answers effort questions interactively** via the MCP tools ("how many FTEs are actually on month-end close?", "which cost centers have people we can't see work for?").
3. **Renders the monthly client pack**: reuses the Boblueprint deck-render step on the narrative + tables.

### What ICA does
1. **Context Studio**: `CostCenter`, `FTEAllocation`, `ProcessArea`, `Project` entities extend the practice base ontology — the effort question becomes graph-queryable and consistent across clients.
2. **Assistant (via `executePrompt`)**: the monthly narrative — changes vs. last month, unallocated-FTE callouts, three reallocation recommendations, data-quality flags instead of guesses.
3. **AAS workflow (optional hardening)**: `Model Runner` → `Narrative agent` → **human review gate** → distribution, scheduled monthly.

### Architecture

```
HR headcount ─┐
Cost centers ─┼─► fte_model.py ─► effort_by_process / unallocated_fte / cost_per_fte
Timesheets  ──┘        │                        │
                       ▼                        ▼
        ICA Context (CostCenter, FTEAllocation graph)   ICA narrative agent ─► HUMAN GATE ─► monthly pack (Bob renders)
```

### Build plan (challenge window)
1. Day 1–2: extract formats agreed; `fte_model.py` against sanitized [CLIENT]-shaped sample.
2. Day 3–4: ontology extension (`CostCenter`, `FTEAllocation`) → Context Studio import (validator-gated).
3. Day 5–6: narrative prompt via `executePrompt`; MCP tools registered in Bob.
4. Day 7–8: monthly schedule (Task Scheduler) + deck render; run on two consecutive months of sample data to show deltas.
5. Day 9–10: before/after evidence; demo recording.

### Code inventory (this folder)
- `fte_model.py` — allocation model + flags + ICA narrative call + MCP tools, one file

### Demo & metric
Live: load month 1 → the unallocated-FTE number appears ("340 FTE in these 12 cost centers have no visible work allocation"); load month 2 → the narrative explains the delta and recommends three moves. Metric: quarterly manual census (weeks of effort) → monthly automatic (minutes), plus the number the client has literally never seen.

### Risks & mitigations
- **Data sensitivity (HR):** aggregate at cost-center level before anything leaves the client boundary; no names in the model.
- **Allocation data missing/dirty:** that *is* the finding — unallocated and unmapped are first-class outputs, not errors.
- **Complexity (Monica's own caution):** scope to join + visibility + narrative; no attempt at activity mining in the window.
