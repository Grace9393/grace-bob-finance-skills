# Video plan & script — Finance Exception Resolution Agent (5:00)

**Presenter:** Joe. **Second voice:** Grace (plays the approver at the gate). See `../video-production-notes.md` for format rules.

| # | Time | On screen | Beat |
|---|---|---|---|
| 1 | 0:00–0:30 | Split screen: ERP exception list, ServiceNow queue, an Excel tracker, an inbox | The pain montage |
| 2 | 0:30–1:00 | One-slide architecture (pipeline diagram from proposal.md) | What we built |
| 3 | 1:00–1:45 | Terminal: `normalize_exceptions.py` run on 50 seeded exceptions | One register |
| 4 | 1:45–2:45 | ICA Agentic App Studio: triage workflow runs, pauses at gate; Grace approves 2 | The gate, on camera |
| 5 | 2:45–3:30 | ServiceNow sandbox: tasks appear; Bob chat: aging summary + drafted follow-up | Action, governed |
| 6 | 3:30–4:15 | Split: Bob building the MCP server (short clip) + the monthly root-cause report | How it's built + "reduce" |
| 7 | 4:15–5:00 | Metric slide + team | Close |

---

## Script

**[1 — 0:00] Joe, over the montage:**
"This is one finance exception. It lives in the ERP as a blocked invoice, in ServiceNow as a ticket, in this spreadsheet as row 47, and in somebody's inbox as a chase email. Nobody owns it, nobody can see how old it is, and a shared-services team spends up to forty percent of its capacity hunting things exactly like it. Every client we serve has this problem. None of them can see it in one place."

**[2 — 0:30] Architecture slide:**
"So we built a governed exception agent with IBM Bob and IBM Consulting Advantage. Three moves: every exception from every source lands in one register. An ICA agent workflow triages and proposes the routing — and pauses for a human to approve. And once a month, Bob analyzes the whole register to answer the better question: how do we stop these exceptions happening at all?"

**[3 — 1:00] Terminal:**
"Watch the register build. Fifty exceptions from three sources — ERP export, ServiceNow, a tracker. One command, written by Bob during this challenge."
*(run; point at output line)* "Fifty exceptions, eleven cross-source duplicates linked automatically — that's eleven things two people were chasing separately without knowing it."

**[4 — 1:45] AAS workflow:**
"The register uploads to an ICA document collection, and the Agentic App Studio workflow takes over. Two agents we built: the Triage agent classifies and diagnoses each exception against the client's process graph in Context Studio — so routing is grounded in who actually owns what. The Routing Proposer drafts the action. And here —" *(workflow pauses)* "— it stops. Nothing executes without approval. Grace?"

**Grace, on camera:** "I'm reviewing the two oldest: a sixty-day unmatched cash item routed to the OTC lead — agreed. A blocked intercompany invoice routed to the wrong team — I'm correcting the owner and approving." *(clicks approve)*

**[5 — 2:45] ServiceNow + Bob:**
**Joe:** "Approved actions execute: two routed tasks, created in ServiceNow, with the approver's name on the record — the tool literally refuses to run without one. And now the question no client can answer today —" *(types in Bob)* "'Show me OTC exceptions aging past thirty days.' One picture, all sources. Bob also drafts the follow-up email. Drafts — the owner sends it."

**[6 — 3:30] Build + reduce:**
"How it's built: Bob wrote the normalizer and this MCP tool server — that's Bob doing what it's for, multi-step work with governance. ICA holds the context graph and runs the workflow with the gate. And the part we're proudest of —" *(root-cause report)* "— monthly, Bob clusters the closed exceptions by root cause. This quarter's answer: three process fixes would eliminate about a third of these exceptions at the source. We're not just handling exceptions faster. We're making them stop."

**[7 — 4:15] Metric slide:**
"The numbers: manual triage, about fifteen minutes per exception. The workflow: the full register in under four minutes, human approval included — timer's been on screen. This runs daily on live engagements from here on; the requirements feed IBM's Enterprise Advantage roadmap. Built in two weeks, on sanitized engagement data, with IBM Bob and ICA as they exist today — and we keep running it after July 22. Thank you."

---

**Word count (spoken):** ~640 — rehearse to 4:30.
**Pre-record checklist:** 50-exception seed file ready; AAS workflow sandbox-tested (fallback: local task queue per FEASIBILITY-PLAN); ServiceNow dev instance logged in if Tier C landed; timer overlay on for beats 3–5; verify the "forty percent of capacity" hook against an engagement data point or soften to "a large share of capacity"; every spoken number must match the screen.
