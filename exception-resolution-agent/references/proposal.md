# Proposal 1 — Finance Exception Resolution Agent (Joe)

**2026 IBMer watsonx Challenge — business proposal + technique**

---

## Business proposal

**Executive summary.** Finance processes fail at the exceptions: unmatched cash, blocked invoices, rejected journals, intercompany breaks. None have a happy flow — they're chased through tickets, mailboxes, and spreadsheet trackers, each one a manual investigation. We deploy a governed agent workflow that consolidates every exception into one register, triages and routes each one with a human approval gate, and — the differentiator — analyzes the register monthly to *reduce* exceptions at the source, not just resolve them faster.

**Client pain & evidence.** In a typical shared-services finance organization, exception handling consumes 20–40% of transactional-team capacity; aging is invisible because ownership is split across ERP workflows, ServiceNow, and email. Every client we serve has this problem; none of them can see it in one place.

**Value.**
- Triage time per exception: ~15 minutes manual → seconds, with the human deciding, not searching.
- One aging picture across all sources for the first time.
- Monthly root-cause clusters convert firefighting into a process-fix backlog — the "reimagine the workflow to minimize exceptions" angle from our kickoff.

**Commercial / asset-based angle.** Consultant-side accelerator on engagements immediately; requirements feed into Enterprise Advantage's roadmap rather than competing with it (we prototype what the product later hardens). Runs on data extracts — no new client infrastructure to sell first.

**2026 fit.** Everyday repeatable usage (the register refreshes daily on live engagements), only Bob + ICA + client's existing ServiceNow, human-in-the-loop by construction.

---

## Technique

### What Bob does
1. **Builds the plumbing** (during the challenge, on camera): the normalizer, the MCP server, the ServiceNow client — Bob writes and iterates this code from plain-English asks.
2. **Acts through governed tools**: with the MCP server registered, Bob answers "what OTC exceptions are aging past 30 days?" and, *after* the approval gate, creates the routed tasks and drafts (never sends) follow-ups.
3. **Monthly reduce-analysis**: Bob reads the register history and produces the root-cause clustering + top-3 process-fix recommendations.

### What ICA does
1. **Context Studio**: the process/owner graph — who owns which process area and system (reuses the Boblueprint base ontology; `ExceptionCase` extends it), so routing recommendations are grounded, not guessed.
2. **Agentic App Studio workflow**: `Exception Triage agent` → `Routing Proposer agent` → **human approval gate** → action tools. Sandbox-test, then run per batch.
3. **Document collection**: each day's register upload is the RAG source the triage agent cites.

### Architecture

```
ERP export ─┐
ServiceNow ─┼─► normalize_exceptions.py ─► exception_register.csv ─► ICA doc collection
trackers  ──┘                                        │
                                                     ▼
                     AAS workflow: Triage agent ─► Routing Proposer ─► HUMAN GATE
                                                     │approved actions
                                                     ▼
                     Bob + exception_mcp.py: create_task / draft_followup / aging queries
                                                     │
                     monthly: Bob root-cause clustering ─► process-fix backlog
```

### Build plan (challenge window)
1. Day 1–2: normalizer against sample extracts (Bob writes it); register schema agreed.
2. Day 3–4: Context Studio graph (owners/processes); doc-collection upload wired.
3. Day 5–6: AAS workflow — two agents + gate; sandbox test with 20 seeded exceptions.
4. Day 7–8: MCP server registered in Bob; ServiceNow sandbox integration.
5. Day 9–10: monthly reduce-analysis prompt; before/after timing capture; demo recording.

### Code inventory (this folder)
- `normalize_exceptions.py` — multi-source ingest → deduplicated register (+ ICA upload hook)
- `exception_mcp.py` — MCP server: aging queries, task creation, follow-up drafting, reduce-analysis feed

### Demo & metric
Live: 50 seeded exceptions across 3 sources → one register → workflow triages and proposes routes → approve two on camera → tasks appear in ServiceNow sandbox → show the root-cause cluster report. Metric: full-register triage in minutes vs. ~15 min/exception manual; plus "top 3 fixes would eliminate N% of last quarter's exceptions."

### Risks & mitigations
- **Roadmap overlap (Adam):** framed as consultant tooling + product feedback channel; we demo on engagement extracts, not a product build.
- **Source-system access:** demo uses extracts + ServiceNow developer sandbox; no production credentials in the challenge.
- **Bad routing:** the gate is structural — nothing executes without approval; routing accuracy is measured against the graph.
