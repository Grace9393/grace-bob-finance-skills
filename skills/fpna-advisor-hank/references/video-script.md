# Video plan & script — "Hank", the FP&A Digital Advisor (5:00)

**Presenter:** Kate. **Second voice:** Adam (plays the business head asking Hank questions). See `../video-production-notes.md`.

| # | Time | On screen | Beat |
|---|---|---|---|
| 1 | 0:00–0:30 | A real (mock) ServiceNow data request, then a calendar showing +3 days | The 3-day round trip |
| 2 | 0:30–1:00 | Architecture slide; "Hank" avatar on the team org chart | Meet Hank |
| 3 | 1:00–2:30 | Bob chat: three cuts in three minutes (timer on) | The teammate demo |
| 4 | 2:30–3:15 | Bob chat: "biggest risks" + a what-if scenario | The advisor demo |
| 5 | 3:15–4:00 | Split: load_data.py TM1/extract paths + ICA industry context + AAS weekly-brief gate | How it's built |
| 6 | 4:00–5:00 | Metric slide (3 days → minutes) + commercial tiers + team | Close |

---

## Script

**[1 — 0:00] Kate, over the ServiceNow request:**
"This is how a CFO team cuts data today. Write a request. Send it to a team three time zones away. Wait three days. Get it back in the wrong format. Repeat. My client asked me last month whether they should outsource more of FP&A — and the honest answer was no. What they need isn't more people cutting data. It's a teammate who cuts it in minutes and never gets tired of 'actually, can I see that by brand instead?'"

**[2 — 0:30] Architecture slide:**
"So we built Hank — a digital member of the FP&A team, powered by IBM Bob and IBM Consulting Advantage. Hank sits on your P&L data — Planning Analytics where you have it, plain extracts where you don't — with three governed tools: cut data, rank variances, run scenarios. Hank never invents a number. Every figure comes from a tool call you can see."

**[3 — 1:00] Bob chat, timer on. Adam types:**
**Adam:** "Hank, cut Q2 gross margin by region."
**Kate:** "Watch the timer — seconds, not days. Table plus two sentences on what stands out — that's Hank's house style."
**Adam:** "Now by brand. And show me actual versus budget versus prior year."
**Kate:** "Same data, new shape, no ticket, no queue. And the third cut — the one that used to be a fresh three-day request —"
**Adam:** "Just EMEA, just the value brands, monthly."
**Kate:** *(pointing at timer)* "Three cuts. Under three minutes. That's the three-day round trip, gone."

**[4 — 2:30] The advisor:**
**Adam:** "Hank, where are my biggest risks?"
**Kate:** "This is the question my clients literally cannot answer today. Hank ranks every actual-versus-budget variance, shows the rows behind each number — citations, not vibes — and look at this line: coverage check. When the data's thin, Hank says so before answering. Now the advisor part:"
**Adam:** "What happens if FX moves two percent against us?"
**Kate:** "Scenario tool: P&L impact, versus budget, in the conversation. That used to be a modeling sprint."

**[5 — 3:15] How it's built:**
"Under the hood: Bob built Hank during this challenge — the data loader, the tools, the persona. Two commercial tiers in one loader: Planning Analytics through its REST API, extending our touchless-forecasting asset — or DuckDB on plain extracts, so a mid-tier client who'll never fund an EPM platform gets Hank for the cost of a laptop. ICA gives Hank the industry context — an FMCG answer and a fintech answer are different, and that context graph is why. And the weekly brief runs as an ICA agent workflow: variance scan, narrative, then a human review gate before anything reaches a stakeholder. Hank advises. People decide."

**[6 — 4:00] Metric slide:**
"The numbers: data cuts, three days to three minutes — you watched the timer. Risk visibility on demand instead of quarter-end. And because Hank is tools plus context, not a platform, it deploys on any client's data in days. The FP&A team keeps using Hank every day after July 22 — that's the point of this year's challenge. Built in two weeks with IBM Bob and ICA as they exist today. Thank you."

---

**Word count (spoken):** ~660 — rehearse to 4:30.
**Pre-record checklist:** `fpna.duckdb` loaded with sanitized extract; MCP server registered; the three cuts + risk + scenario prompts rehearsed; timer overlay for beats 3–4; coverage-check line visible in the risk answer.
