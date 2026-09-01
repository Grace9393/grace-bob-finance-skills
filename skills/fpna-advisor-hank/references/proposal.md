# Proposal 2 — "Hank": the FP&A Digital Advisor (Kate)

**2026 IBMer watsonx Challenge — business proposal + technique**

---

## Business proposal

**Executive summary.** FP&A teams can't answer "where are my biggest risks?" from their own data. Cutting data means a ServiceNow request to an offshore team and a three-day round trip — then another when the format is wrong. We put a humanized digital teammate — Hank — on the team: ask in plain English, get the cut in minutes, ask again in a different shape, then ask *why* and get driver-ranked advice grounded in the numbers and the client's industry context.

**Client pain & evidence.** Kate's live client asked to outsource more of FP&A; the honest answer was that a digital workforce beats outsourcing because the need is *iterative* data cutting, not volume. Yushi: FP&A information sits in unstructured Excels. The advisor layer — scenario runs on demand for business heads — is the most-requested, least-served capability in the CFO office (three votes in our own kickoff).

**Value.**
- Data-cut turnaround: ~3 days → under 5 minutes, iterations free.
- Risk visibility: top variances ranked with drivers, on demand, not quarter-end.
- Scenario runs: what-ifs (volume, price, FX) in the conversation, not a modeling sprint.

**Commercial / asset-based angle.** Two tiers: Planning Analytics (TM1) as the data spine where the client has it — direct extension of our touchless-forecasting asset — and DuckDB-on-extracts for mid-tier clients who will never fund an Apptio-class platform (Kate's UBS lesson). Industry nuance comes from the ICA context, which is our differentiation vs. generic copilots.

**2026 fit.** Daily-usage tool by definition; human stays the decision-maker (Hank advises, cites, and never invents numbers); Bob + ICA + existing portfolio only.

---

## Technique

### What Bob does
1. **Builds Hank** during the challenge: the data loader, the DuckDB model, the MCP server — written and iterated by Bob from plain-English asks (this is itself demo content).
2. **Is Hank's runtime**: with the MCP server registered, Bob *is* the conversational surface — the persona prompt makes it a teammate ("cut Q2 gross margin by region… now by brand").
3. **Writes the narrative**: driver commentary on any cut, and the weekly brief draft.

### What ICA does
1. **Context Studio**: industry reference corpus (from the Boblueprint harvest pipeline) so advice carries FMCG vs. fintech vs. education nuance — the thing generic copilots can't do.
2. **Agentic App Studio workflow**: the *weekly proactive brief* — `Variance Scanner agent` → `Narrative agent` → **human review gate** → distribution. Hank answering questions is interactive Bob; the recurring brief is the governed ICA workflow.
3. **Assistant variant**: an ICA assistant with the same tools serves stakeholders who live in ICA rather than Bob.

### Architecture

```
Planning Analytics (TM1 REST) ──┐
ERP/EPM extracts (xlsx/csv) ────┼─► load_data.py ─► fpna.duckdb
                                │                      │
                                ▼                      ▼
            ICA Context (industry corpus)     hank_mcp.py (cut_data / top_variances / run_scenario)
                                │                      │
                                └───────► Bob-as-Hank ◄┘   ...and weekly: AAS Scanner→Narrative→GATE→brief
```

### Build plan (challenge window)
1. Day 1–2: `load_data.py` against a sanitized client extract; star-schema `pnl` table agreed.
2. Day 3–4: `hank_mcp.py` three core tools; persona prompt tuned; first live cuts.
3. Day 5–6: TM1 REST connector against the touchless-forecasting sandbox cube.
4. Day 7: ICA industry context (harvest pipeline reuse); grounding rules in the persona.
5. Day 8–9: AAS weekly-brief workflow with review gate; sandbox test.
6. Day 10: before/after timing capture; record the "three cuts in three minutes" demo.

### Code inventory (this folder)
- `load_data.py` — extracts/TM1 → DuckDB star schema
- `hank_mcp.py` — MCP server: `cut_data`, `top_variances`, `run_scenario`, `weekly_brief_feed` + the Hank persona prompt

### Demo & metric
Live: business head asks Hank for a cut, reshapes it twice, then "what are my three biggest risks and what would you do?" — answers cite cells. Metric: 3-day round trip → minutes, on stage; scenario run that used to be a modeling request handled in-conversation.

### Risks & mitigations
- **Data quality:** Hank reports coverage gaps instead of guessing (tool returns row counts + nulls; persona forbids invented numbers).
- **"EPM replacement?" objection:** No — advisor layer on top; PA/EPM where it exists, extracts where it doesn't (this is the answer the kickoff aligned on).
- **Sensitivity:** sanitized [INTERNAL] extract for the challenge; client deployments run inside their tenancy.
