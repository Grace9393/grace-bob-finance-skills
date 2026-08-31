---
name: rfp-response
description: Build a winning RFP, RFI or proposal response — qualify the bid, deconstruct the document into a traceable requirement and compliance matrix, develop win themes against the stated evaluation criteria, draft the response, price it, and run the review gates. Also covers issuing an RFP on a client's behalf for vendor selection. Use when the user mentions RFP, RFI, RFQ, ITT, tender, bid, proposal response, compliance matrix, evaluation criteria, win themes, bid/no-bid, red team review, or vendor selection.
---

# RFP Response — conduct guide

You are building a response that must survive a scored evaluation by people who will not meet you.
Two truths govern everything below:

1. **Evaluators score against their criteria, not against your quality.** An excellent answer to a
   question they did not ask scores zero. Compliance is the floor; differentiation only earns
   points once compliance is proven.
2. **Non-compliance is usually fatal and usually procedural** — a missed mandatory form, a late
   submission, an exceeded page limit, an unanswered sub-question. Run the mechanics first and the
   prose last.

## Step 1 — Qualify (bid / no-bid)

Before any writing. Score the opportunity honestly on the eight tests in
`references/rfp-playbook.md` §1: is there a real budget and a decision date · do we know the
client before the RFP · can we meet every mandatory requirement · is the incumbent or a shaped
competitor already positioned · does the evaluation model favour us · do we have the delivery
capacity and references · is the commercial model acceptable · is the effort proportionate.

Produce a written recommendation with the reasons. **A no-bid is a legitimate output of this
skill** — say so plainly when the evidence points there, rather than defaulting to bid.

## Step 2 — Deconstruct the document

Extract every requirement into a traceable register. For a text RFP:

```
python scripts/rfp_compliance.py extract rfp.txt --out requirements.csv
```

This pulls candidate requirements (shall / must / should / will / is required to), tags each
`mandatory` or `desirable`, and keeps the section reference. For a Word or PDF RFP, extract the
text first with `07-contract-review/scripts/contract_extract.py`, then run the command above.

**The extraction is a draft, not the answer.** Review every row: the parser will miss requirements
buried in tables, appendices and evaluation criteria, and it will over-capture boilerplate. Add
what it missed by hand — a missed mandatory requirement is the most expensive defect in this
process.

Then capture the **mechanics** separately, because they disqualify: submission deadline and
timezone, format, page and font limits, file naming, portal or email address, mandatory forms and
certificates, question deadline, validity period, and the evaluation weightings.

## Step 3 — Build the compliance matrix

```
python scripts/rfp_compliance.py matrix requirements.csv --xlsx Compliance_Matrix.xlsx
```

Every requirement gets an owner, a compliance status (`compliant` / `partial` / `alternative` /
`non-compliant`), the response location, and the evidence or proof point. The script reports
coverage, unassigned rows, and — the check that matters — **every mandatory requirement not yet
compliant**. Nothing else proceeds while that list is non-empty.

**Gate 1:** no unowned requirements, and a decision recorded for every mandatory item. A `partial`
or `alternative` is a legitimate position; an unnoticed gap is not.

## Step 4 — Win themes and solution

Win themes are built from the client's stated evaluation criteria and their known priorities, not
from your capability list. Each theme follows the discipline in `references/rfp-playbook.md` §4:
**client issue → our approach → the proof → the quantified benefit to them**. Three to five themes,
each traceable to a scored criterion, each carrying evidence — a named reference, a metric, a
credential.

Where the response is a finance transformation, take the substance from the assessment skill (08):
benchmarks from its benchmark library, the diagnosis from its pain-point taxonomy, the phasing and
business case from its roadmap pack. A proposal that reuses a real assessment structure reads as
delivery experience rather than marketing.

## Step 5 — Draft

Follow the response outline in `assets/rfp-response-outline.md` and the writing rules in
`references/rfp-playbook.md` §5. The rules that move scores most:

- **Answer in the client's structure and their words.** Mirror their section numbering exactly.
- **Answer the question in the first sentence.** Evaluators score the first paragraph.
- **Specific beats superlative.** <!-- house-style: allow -->
  "43 finance transformations in the last three years, of which 11
  in your sector" outscores "world-class experience" every time.
- **Every claim carries evidence**; every benefit carries a number and its basis.
- **Name the risks and how you manage them.** Responses with no risks read as inexperienced.

Insert `[SENIOR REVIEW]` wherever content is asserted rather than evidenced, and list every marker
at handover. Never invent a client reference, a credential, a certification or a metric — if the
proof does not exist, the honest position is a weaker claim, not a fabricated one.

House style binds proposals as it binds every other deliverable: active voice, present tense,
sentences averaging ~18 words, no marketing words, no filler hedges. Lint before the review gates:

```
python ../08-finance-transformation-assessment/scripts/ft_house_style.py <draft>
```

The rules and the rationale are in
`08-finance-transformation-assessment/references/house-style-and-blueprint-contract.md` §5.

## Step 6 — Price

Pricing structure, the pricing narrative, and the traps (unpriced assumptions, unbounded scope,
indexation, FX, T&M vs fixed vs outcome-based) are in `references/rfp-playbook.md` §6. Every
assumption that shapes the price is stated in the response — an unstated assumption becomes the
client's to interpret, and they will interpret it against you.

Commercial terms, liability, IP and indemnities: review with the `contract-review` skill (07)
before submission, from the supplier/IBM position.

## Step 7 — Review gates

Three passes, in order — details in `references/rfp-playbook.md` §7:
1. **Compliance check** — rerun the matrix. Every mandatory requirement answered; mechanics met.
2. **Score-the-response** — someone who did not write it scores it against the published criteria
   as an evaluator would, and reports the score with reasons.
3. **Red team** — attack it: where is it generic, unevidenced, non-responsive, or beaten by the
   likely competitor?

**Gate 2:** submit only when the mandatory list is clear, all `[SENIOR REVIEW]` markers are
resolved, and the mechanics checklist is fully ticked. Submit early — portals fail at deadlines.

## Issuing an RFP for a client

The same machinery runs in reverse when you help a client select a vendor: requirement register →
weighted evaluation criteria published up front → response template that forces comparability →
scoring model → shortlist and demo script. See `references/rfp-playbook.md` §8. Keep scoring
weights agreed *before* responses arrive; weights set afterwards are indefensible in a challenge.

## References
- `references/rfp-playbook.md` — qualification tests, RFP anatomy, evaluation mechanics,
  compliance discipline, win themes, writing rules, pricing, review gates, issuing an RFP.
- `assets/rfp-response-outline.md` — the response skeleton with what belongs in each section.
- `assets/requirements-template.csv` — worked requirement register / compliance matrix.
- Related skills: `finance-transformation-assessment` (08) for the substance,
  `contract-review` (07) for terms, `ar-diagnostic` (06) for AR-specific scope.
