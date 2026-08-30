---
name: contract-review
description: Review a contract, agreement, SOW, or Transaction Agreement (TA) before signature — extract text/comments/placeholders from the docx, run the 8-check internal-consistency sweep (annex↔scope match, timeline math, arithmetic, cross-references), apply the position-aware CUAD-derived risk checklist, and produce a severity-ranked findings report with a signable/not-signable verdict. Use when the user asks to review, check, redline, or risk-assess a contract, agreement, TA, SOW, MSA, NDA, or DPA, or asks "what should we be careful about" in a legal document.
---

# Contract review — conduct guide

You are reviewing a contract for signability. Two hard rules:
1. **Only cite text actually present in the document** — quote it. Anything that
   depends on a document not provided (e.g. the incorporated MSA) goes under
   "Points to verify," never assumed.
2. **This is an informational review, not legal advice** — material terms are
   escalated to counsel; the report must say so.

## Step 1 — Extract

For a `.docx`, run:

```
python scripts/contract_extract.py "path/to/contract.docx" -o extracted/
```

This yields `contract_text.txt` (body), `comments.md` (reviewer comments with
author/date), and `review_flags.md` (placeholders, tracked changes, headers/
footers). For PDF, extract text with available tools; note if scanned. Read the
**whole** contract before flagging anything.

## Step 2 — Classify and take a position

Identify: document type (TA/SOW under MSA, standalone MSA, NDA, DPA…), the
parties, incorporated documents, and **whose side we review for** (default:
Supplier / IBM side). State the position in the report header — severity is
position-dependent (`references/contract-review-checklist.md` §1).

## Step 3 — Internal-consistency sweep (highest yield — do this before clause risk)

Run all eight checks in `references/consulting-ta-review-patterns.md`:
annex↔body↔scope match · scope contradictions vs charges · timeline math (term
vs invoicing vs acceptance-cycle days, impossible notice periods, undefined date
anchors) · arithmetic re-computation of every charge table · cross-reference
integrity · defined-term consistency · party/authority structure · pre-signature
hygiene (open comments incorporated? placeholders filled?). Assembly defects
found here (wrong annex, priced-but-excluded services) outrank any clause issue.

## Step 4 — Clause risk analysis

Walk the risk domains in `references/contract-review-checklist.md` §2 with the
severity ladder (🔴/🟡/🟢) and market benchmarks (§3). For the supplier side,
apply the clause watchlist in the patterns file: record favorable clauses under
"Preserve" so they survive redlining, and push-back items with ask + fallback.

## Step 5 — Report

Follow the output format in the checklist §6: header with position and overall
risk → bottom line (signable / signable-after-fixes / not signable, and the
single biggest issue first) → critical issues with quotes and proposed fixes →
internal inconsistencies → points to verify → unresolved comments → favorable
clauses to keep → negotiation priority table → disclaimer.

## Gates
- Never mark "signable as-is" while any placeholder, open comment, or
  unaccepted tracked change remains — hygiene flags block signature.
- If the MSA or any incorporated document was not provided, the verdict is at
  best "signable after listed fixes" with the MSA-dependent items listed.
- Redlines are proposals; contract edits and signature routing are done by
  humans with authority.

## References
- `references/contract-review-checklist.md` — consolidated CUAD-derived risk
  domains, severity/position logic, market benchmarks, negotiability, 7 C's
  screen, report format, guardrails. Sources credited in-file.
- `references/consulting-ta-review-patterns.md` — the 8-check internal-
  consistency sweep for TAs/SOWs under an MSA, supplier-side clause watchlist,
  verdict framing. Built from a real 2026 TA review.
