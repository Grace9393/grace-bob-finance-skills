# Proposal 5 — Client-Specific "Ask Finance" (Tui)

**2026 IBMer watsonx Challenge — business proposal + technique**

---

## Business proposal

**Executive summary.** Ask Finance answers generically: ask "how do we improve cash performance this quarter?" and you get textbook advice, not *your* quarter's levers. We build the grounded version: a governed, tenant-isolated assistant over one client's (or IBM's own, ClientZero) actual close pack, AR aging, and cash data — every answer cited to a document and figure, or an explicit "the data doesn't support an answer, here's what's missing." The build is mostly governance, because that's the real blocker: sanitization before anything moves, per-role assistants, and a grounding-score eval harness that gates the demo.

**Client pain & evidence.** Tui tested the launched Ask Finance with real example questions: it "will give you very generic advice but it won't have the specifics of the performance of that quarter." Every internal finance use case we've tried hits the same wall — and then hits data-access and sensitivity issues, which is why governance is the product here, not a compliance afterthought.

**Value.**
- Quarter-specific, cited answers to the questions CFO teams actually ask ("what drove the DSO increase?", "top three cash levers *this* quarter?").
- Refuses instead of hallucinating — grounding score measured, not asserted.
- A pattern (sanitize → tenant-isolated RAG → grounded assistant → eval) reusable for any sensitive-data agent, which is worth more than the single use case.

**Commercial angle.** The demo IBM's own finance can use (ClientZero, per the kickoff), and the objection-handler for every client who says "our data is too sensitive for AI" — because the governance pattern *is* the deliverable. Feeds requirements to the Ask Finance product team.

**2026 fit.** Weekly/daily usage by finance teams; human validates recommendations; Bob + ICA only; the sensitivity risk the team raised is addressed structurally.

---

## Technique

### What Bob does
1. **Builds the governance tooling**: the sanitizer, the upload pipeline, the eval harness — written and iterated by Bob during the challenge.
2. **Runs the eval loop**: Bob executes the golden-question harness, reads the failures, and tunes the assistant prompt until the grounding score passes threshold — a visible, honest quality loop for the judges.
3. **Drafts the weekly insights brief** from the assistant's cited answers (human reviews).

### What ICA does
1. **Document collections (tenant-isolated RAG)**: the sanitized quarter pack lives inside the ICA tenant — data never leaves governed storage; this is the sensitivity answer.
2. **Grounded assistant**: system prompt enforces cite-or-refuse; `collectionId` scopes every query to the governed dataset.
3. **Per-role assistants**: CFO view vs. analyst view — separate assistants over role-appropriate collections rather than one all-access bot.

### Architecture

```
close pack / AR aging / cash reports
        │  sanitize (DLP scrub — names, account numbers)
        ▼
askfinance.py upload ─► ICA document collection (tenant-isolated, per role)
        │
        ▼
grounded assistant (cite-or-refuse system prompt) ◄── executePrompt(collectionId)
        │                                                   ▲
        ▼                                                   │
   eval harness: golden questions → grounding score ── Bob tunes until ≥ threshold
```

### Build plan (challenge window)
1. Day 1–2: assemble the ClientZero quarter pack (sanitized extracts agreed with data owner).
2. Day 3: sanitizer + upload; collection created; spot-check scrubbing.
3. Day 4–5: grounded-assistant system prompt; first cited answers.
4. Day 6–7: golden-question eval harness; Bob tunes to threshold (target ≥ 80% grounded).
5. Day 8–9: per-role split (CFO/analyst); side-by-side demo vs. generic Ask Finance.
6. Day 10: record demo; document the governance pattern as the reusable asset.

### Code inventory (this folder)
- `askfinance.py` — sanitizer, collection upload, grounded query, golden-question eval harness, one file

### Demo & metric
Side-by-side on stage: the same question to generic Ask Finance (textbook advice) and to this (three levers, each cited to the quarter's documents). Metric: grounding score on the golden set (target ≥ 80%), and the refusal behavior shown live on a question the data can't answer.

### Risks & mitigations
- **Data sensitivity (the big one):** sanitized ClientZero extracts only during the challenge; DLP scrub before upload; tenant isolation; per-role assistants; no production credentials.
- **Hallucination:** cite-or-refuse prompt + measured grounding score + refusal demo — the failure mode is governed, not hidden.
- **Scrubber quality:** the regex scrub is the challenge-window stand-in; the doc names the client's DLP tool as the production path.
