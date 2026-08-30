# Contract review checklist — consolidated

Consolidated from: CUAD risk taxonomy (41 categories, 510 real contracts) as adapted by
[evolsb/claude-legal-skill](https://github.com/evolsb/claude-legal-skill) (MIT),
[claude-office-skills/contract-review-skill](https://github.com/claude-office-skills/contract-review-skill),
the Lawvable review-and-redline playbook pattern (traffic-light severity), the
"7 C's" SOW review heuristic (Precursive), and our own consulting-TA review practice
(see `consulting-ta-review-patterns.md`).

## 1. Position-aware severity

Always establish **whose side we review for** before flagging anything. Default for
our engagements: **Supplier (IBM) side**.

| Severity | Meaning |
|---|---|
| 🔴 Critical | Threatens core interests of our position, or makes the contract unsignable (wrong annex, impossible clause, unbounded liability) |
| 🟡 Important | Material but negotiable; needs a decision or a redline |
| 🟢 Acceptable | Market-standard or favorable to our position — record it so it isn't "fixed" away |

Position flips risk: a deemed-acceptance clause is 🟢 for the supplier, 🟡/🔴 for the
customer. Never review without declaring the position in the report header.

## 2. Risk domains (CUAD-derived, trimmed to professional services)

- **Document basics** — parties and legal entities, effective/commencement dates,
  contract numbers, placeholders, execution status, signature authority.
- **Term & termination** — duration, extension mechanics (are the notice periods
  physically possible within the term?), termination for convenience/cause, cure
  periods, survival of acceptance/payment/confidentiality past expiry.
- **Scope & deliverables** — deliverables enumerated and matched to acceptance
  criteria; in-scope vs out-of-scope lists consistent with the charges; advisory vs
  implementation language ("diagnostic in nature" protects the supplier).
- **Financial terms** — pricing model per component (FP/T&M), rate cards, invoicing
  schedule, expense handling (pre-approval?), currency/VAT treatment, volume-commit
  interactions, price-increase caps.
- **Acceptance** — review window, deemed acceptance on silence, number of revision
  cycles, escalation path, turnaround times feasible for both sides.
- **Liability & risk** — cap amount and basis (per MSA?), carve-outs, indemnities,
  warranties, exclusive remedies, responsibility for customer/third-party systems,
  non-binding-estimates language.
- **IP & confidentiality** — deliverable IP vs supplier tools/AI-systems IP,
  pre-existing materials, license-back, residual knowledge, non-disparagement.
- **AI & data** — approved AI systems list, who manages access, what happens to AI
  tooling at expiry, DPA/personal-data annex matches the actual engagement, approved
  sub-processors, cross-border transfer mechanism.
- **Dependencies & assumptions** — customer-supplied items, stakeholder availability,
  data-delivery lead times, delay-relief mechanism (Change Request), reliance on
  customer data without independent verification.
- **Dispute & governing law** — governing law, escalation/governance body, arbitration,
  offshore-jurisdiction flags.

## 3. Market benchmarks (yellow/red thresholds)

| Provision | Standard | 🟡 | 🔴 |
|---|---|---|---|
| Liability cap | 12 months' fees | 6–11 months | <6 months or uncapped exposure |
| Acceptance review window | 5–10 business days w/ deemed acceptance | no deemed acceptance | unlimited review |
| Revision cycles | 1–2 then escalate | 3+ | unlimited |
| Supplier revision turnaround | 5+ business days | 3–4 | <3 |
| Auto-renewal / extension notice | ≤30 days on short TAs | notice ≥ remaining term | notice > full term (impossible) |
| Price increase cap | CPI or 5%/yr | 10%/yr | uncapped |
| Data export on exit | 90 days, standard format | 30 days | none |

## 4. SOW "7 C's" quick screen

Clarity (a new reader understands scope) · Commerciality (pricing model matches
delivery risk) · Credibility (deliverables match team and timeline) · Collaboration
(client inputs written as dependencies) · Cadence (reporting rhythm defined) ·
Control (change control and decision rights) · Closure (acceptance and exit criteria
explicit).

## 5. Negotiability guide

- **High:** cure periods, revision turnarounds, data-delivery lead times, expense caps.
- **Medium:** liability cap multipliers, acceptance windows, IP license scope.
- **Low:** MSA-flowdown terms, regulatory/DPA mandates.
- **None:** statutory requirements. Don't spend negotiation capital on Low/None.

## 6. Report output format

1. **Header** — document, version, parties, our position, overall risk 🔴🟡🟢.
2. **Bottom line** — one paragraph: signable or not, and the single biggest issue.
3. **Critical issues** — numbered; each with quoted text (≤125 chars), why it matters,
   proposed fix/redline, fallback.
4. **Internal inconsistencies** — from the consistency sweep (see patterns file).
5. **Points to verify** — facts we could not confirm (authority, MSA terms not provided).
6. **Unresolved comments / tracked changes** — from extraction.
7. **Favorable & acceptable** — what to *keep*; protects good clauses during redlining.
8. **Negotiation priority table** — issue / ask / fallback / negotiability.
9. **Disclaimer** — informational review, not legal advice; material terms go to counsel.

## 7. Guardrails

- Only cite text actually present in the document; quote it.
- If the MSA (or any incorporated document) is not provided, list every clause that
  depends on it under "Points to verify" — never assume its content.
- Executed contracts: review is informational only; no redlines.
- Show uncertainty explicitly when interpretation is ambiguous.
