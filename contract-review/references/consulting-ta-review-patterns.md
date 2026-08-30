# Consulting TA/SOW review patterns — the internal-consistency sweep

Generic legal checklists catch clause-level risk. In consulting Transaction
Agreements / SOWs issued under an MSA, the highest-value findings are usually
**assembly defects**: annexes pasted from other deals, dates that don't add up,
cross-references to sections that don't exist. This sweep catches them. Every
pattern below was observed in a real TA draft (v1.3, 2026) that had passed
multiple human reviews.

## The sweep — run all eight checks

### 1. Annex ↔ body ↔ scope match (highest yield)
Read the Services description, then read the Charges annex **as if it were the
only document**. Do the priced components describe the same engagement?
- Red flags: component names from another program (different product names,
  different phase names), deliverables in the charge table that appear nowhere in
  the services annex, order-of-magnitude mismatch between effort and price.
- *Observed:* a 4-week advisory assessment carrying a ~700K USD charges annex
  priced for a different program's testing + change-management + sustain scope.
- Also check the **personal-data annex**: do the data-subject categories match
  the engagement? (An AR engagement processes debtor/customer data, not
  procurement supplier contacts.)

### 2. Scope contradiction
Cross out-of-scope lists against the charges. Anything both **excluded in the
services annex and priced in the charges annex** (e.g. "PMO services") is a
contradiction — and note which document prevails under the order-of-precedence
clause.

### 3. Timeline math
- TA term vs invoicing schedule: no invoice month may fall after expiry.
- TA term vs acceptance process: sum the review-cycle business days
  (submission + review + revision + re-review + validation) from the Week-4
  delivery date — does acceptance complete before expiry? If not, require
  survival language.
- Impossible clauses: extension notice period longer than the whole term.
- Undefined anchors: deliverable due dates keyed to a "Services Commencement
  Date" that is set to N/A.

### 4. Arithmetic verification
Recompute every table: line items vs stated totals, rate × days vs line totals,
component totals vs grand total, split percentages. Flag: totals that differ by
1 (rounding vs error), decimal-separator typos (`47.783.1`), rates that are
5–10× the same band's other rates, year typos in schedules (Jan "2026" after
Dec 2026).

### 5. Cross-reference integrity
Every "Annex X", "Section N.N", "Module/Part" reference must resolve to
something that exists in the TA or the MSA. Common failure: sub-annex tables
referencing "Annex 1" when the TA uses letters.

### 6. Defined-term consistency
Every capitalized term is either defined in the TA, defined in the MSA, or
flagged. Watch near-misses: "Supplier AI Tools" used where "Supplier AI
Systems" is defined.

### 7. Party & authority structure
Issuing entity vs MSA signatory entity: if the TA customer is an affiliate of
the MSA's "Customer Main Party", verify the MSA's affiliate-ordering provisions
allow it. A signature block marked "for internal use only (not a contract
party)" is a tell that this needs checking.

### 8. Pre-signature hygiene
Run `scripts/contract_extract.py` — it reports placeholders (`[...]`, `XXXXX`,
`TBD`), unresolved Word comments, unaccepted tracked changes, and header/footer
text. Every open comment must be resolved-and-stripped; check whether comment
requests were actually incorporated in the body (compare comment text against
the current text).

## Supplier-position clause watchlist (IBM side)

**Preserve — do not let these be negotiated away:**
- Deemed acceptance after a fixed review window.
- Revision cycles capped (1–2) with escalation to governance.
- "Supplier may rely on Customer-provided information without independent
  verification."
- No responsibility for customer/third-party system failures.
- Estimates/projections expressly non-binding.
- Advisory-only scope language + explicit out-of-scope list.
- Delay-relief assumption: late customer inputs → schedule adjustment via
  Change Request.
- Supplier AI Systems remain supplier IP; customer access ends at expiry.

**Push back / verify:**
- Supplier revision turnaround <5 business days on consolidated feedback.
- Customer data-delivery lead times that are impossible in week 1 of a short
  engagement (data due 5 business days before a workshop that happens in the
  first week).
- Expense pre-approval per-expense (prefer a pre-approved travel budget).
- Value Assurance / Exit Assistance flow-downs on short diagnostics — confirm
  they are disapplied.
- Any obligation keyed to MSA sections not provided for review.

## Verdict framing

End every review with one of:
- **Signable as-is** (only 🟢/minor 🟡 findings)
- **Signable after listed fixes** (🟡 findings, no structural defects)
- **Not signable in current form** (any 🔴 assembly defect: wrong annex,
  charges/scope contradiction, broken party structure)
