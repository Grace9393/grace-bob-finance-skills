# Video plan & script — FTE Effort & Cost-Center Visibility (5:00)

**Presenter:** Monica. **Second voice:** the lead (plays the client asking the unanswerable question). See `../video-production-notes.md`.

| # | Time | On screen | Beat |
|---|---|---|---|
| 1 | 0:00–0:30 | Org chart + cost-center report + project plan, disconnected | The unanswerable question |
| 2 | 0:30–1:00 | Architecture slide | What we built |
| 3 | 1:00–2:00 | Terminal: `fte_model.py` runs on month 1; the unallocated-FTE number reveals | The number nobody has seen |
| 4 | 2:00–2:45 | Bob chat via MCP tools: effort questions answered live | Ask anything |
| 5 | 2:45–3:30 | Month 2 runs; ICA narrative with deltas; human review gate | Monthly, governed |
| 6 | 3:30–4:15 | Split: Bob building the model + Context Studio entities | How it's built |
| 7 | 4:15–5:00 | Metric slide + team | Close |

---

## Script

**[1 — 0:00] Lead, on camera:**
"How many people do we actually have working on month-end close?"

**Monica, over the disconnected screens:**
"That question came from a real client — and they couldn't answer it. Headcount lives in HR. Cost lives in cost centers. Work lives in projects and timesheets. Nobody joins them. So transformation programs baseline effort with a manual census that takes weeks and is stale before it's finished. They know what needs to be done. They don't know how many people they have on it."

**[2 — 0:30] Architecture slide:**
"We built the join, with IBM Bob and IBM Consulting Advantage. Three extracts in — headcount, cost centers, allocations. A monthly model out: effort by process, cost per FTE, and one number that has never existed before at our clients: unallocated FTE. The people the organization is paying whose work nobody can see."

**[3 — 1:00] Terminal, month 1:**
"Watch month one. Three files, one command — Bob wrote this model during the challenge. Aggregated at cost-center level; no employee names ever leave the client boundary." *(run; output appears)* "There it is. Eight hundred and seventy-nine FTE of invisible effort — and four hundred and twenty-four of it concentrated in just six cost centers with almost no work allocation at all. That's not a data error — that's the finding. This client has a nine-figure payroll and this number was invisible until now."

**[4 — 2:00] Bob chat:**
"And now the client's question, answered in seconds:" *(types)* "'How many FTEs are actually on month-end close?' — 41.5, with the cost centers behind it. 'Which cost centers have the most invisible effort?' — ranked, with cost-per-FTE context. This is Bob using governed tools over the model — it can't invent a number, it can only read what the model computed."

**[5 — 2:45] Month 2 + narrative:**
"This is monthly, not a one-off. Month two runs, and the ICA narrative agent explains the delta: where effort moved, which cost centers cleaned up their allocations, three reallocation recommendations with evidence — and data-quality flags where the extracts are dirty, instead of guesses. It's drafted by the agent, reviewed by a consultant at the gate, and only then does it reach the client pack, which Bob renders in our branded format."

**[6 — 3:30] How it's built:**
"How it's built: Bob wrote the allocation model, the tools, and renders the monthly deck. ICA holds the structure — CostCenter and FTEAllocation entities extend our practice ontology in Context Studio, so the effort question is graph-consistent across every client we run this for — and the narrative agent runs behind a human review gate. Client extracts, Bob, ICA. Nothing else."

**[7 — 4:15] Metric slide:**
"The numbers: a quarterly manual census that took weeks becomes a monthly automatic run that takes minutes. And the unallocated-FTE number — the one that was invisible — is now on the first page of the client's monthly pack. We're running this on a live engagement structure from here on, every month, after July 22. Built in two weeks with IBM Bob and ICA as they exist today. Thank you."

---

**Word count (spoken):** ~600 — rehearse to 4:30.
**Pre-record checklist:** two months of sanitized Heineken-shaped sample data; the reveal numbers verified against the actual run (current sample: 879 total / 424 in the six dark cost centers — regenerate if the seed changes); MCP tools registered for beat 4; narrative pre-generated for beat 5 (label if shown at speed).
