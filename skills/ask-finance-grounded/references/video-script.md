# Video plan & script — Client-Specific "Ask Finance" (5:00)

**Presenter:** Tui. **Second voice:** Yushi (asks the questions in both windows). See `../video-production-notes.md`.

| # | Time | On screen | Beat |
|---|---|---|---|
| 1 | 0:00–0:40 | Side-by-side: generic Ask Finance vs. an empty second window | The generic-advice problem, shown not told |
| 2 | 0:40–1:10 | Architecture slide — governance pipeline front and center | What we built (governance IS the product) |
| 3 | 1:10–1:50 | Terminal: sanitize with redaction counts → upload to tenant collection | Data never moves raw |
| 4 | 1:50–3:00 | The side-by-side pays off: same question, cited quarter-specific answer | The money shot |
| 5 | 3:00–3:40 | The refusal: a question the data can't answer | Governed failure mode |
| 6 | 3:40–4:20 | Eval harness runs; grounding score; Bob tuning loop | Measured, not asserted |
| 7 | 4:20–5:00 | Metric slide + reusable-pattern claim + team | Close |

---

## Script

**[1 — 0:00] Tui, over the left window:**
**Yushi:** *(types into generic Ask Finance)* "How do we improve cash performance this quarter?"
**Tui:** "Watch the answer: accelerate collections, review payment terms, optimize inventory. All true. All useless — it's textbook advice that fits every company on earth, because the tool has never seen this company's quarter. When we tested the finance use cases internally, this is the wall every one of them hit. And the moment you try to fix it with real data, you hit the second wall: sensitivity and access."

**[2 — 0:40] Architecture slide:**
"So we built the grounded version — and made governance the product, not the afterthought. IBM Bob plus IBM Consulting Advantage: sanitize before anything moves, load into a tenant-isolated ICA document collection, answer only with citations from that collection — or refuse — and measure the grounding with an eval harness before anyone is allowed to demo it. Including us. Everything you're about to see runs on sanitized [INTERNAL] data."

**[3 — 1:10] Terminal:**
"Step one, the scrubber Bob wrote: account numbers, IBANs, emails, names — redacted before upload, with counts per file so the data owner can verify." *(run; point at the printed total — say that number, never a rehearsed one)* "Step two: the quarter pack — close reports, AR aging, cash flow — into an ICA document collection. Tenant-isolated. The data never leaves governed storage, and there's a separate collection per role — the CFO view and the analyst view are different assistants."

**[4 — 1:50] Side-by-side:**
**Yushi:** *(same question, right window)* "How do we improve cash performance this quarter?"
**Tui:** "Now look at the difference. Three levers, ranked: overdue receivables past sixty days concentrated in EMEA — cited to the AR aging file, page and figure. Early-payment discounts costing more than they return — cited to the cash report. And the close-calendar misses that delayed two billing runs — cited. Same question. But this answer knows what quarter it is."

**[5 — 3:00] The refusal:**
**Yushi:** "What will revenue be in five years?"
**Tui:** "And it refuses — 'the data doesn't support an answer; here's what's missing.' That's not a limitation, that's the feature. A grounded assistant that guesses is worse than a generic one, because people believe it."

**[6 — 3:40] Eval harness:**
"How do we know it stays honest? We measure it. A golden-question set with known answers — including questions that must be refused — runs against every version." *(harness runs; read the score off the screen)* "That's the live score against our eighty-percent gate. When it fails, Bob reads the failures and tunes the assistant prompt — that loop, Bob tuning against a measured score, is how this was built in two weeks."

**[7 — 4:20] Metric slide:**
"The numbers: generic advice to cited, quarter-specific levers — you saw it side by side. Grounding measured live against an eighty-percent gate, with refusal behavior proven on camera. And the bigger asset: the pattern — sanitize, isolate, ground, evaluate — is reusable for every 'our data is too sensitive for AI' conversation we have with clients, which is all of them. IBM's own finance team can use this after July 22, and the requirements feed the Ask Finance product roadmap. Built with IBM Bob and ICA as they exist today. Thank you."

---

**Word count (spoken):** ~640 — rehearse to 4:30.
**Pre-record checklist:** generic Ask Finance window ready (confirm nothing sensitive on screen); sanitized [INTERNAL] quarter pack approved by data owner; golden set passing ≥80% the night before; the refusal question rehearsed; redaction-count output visible in beat 3.
