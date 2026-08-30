---
name: sop-rules-register
description: Extract a business rules register and a tribal knowledge register from an SOP corpus — every threshold, approval limit, routing rule, account-specific exception, field mapping and validation requirement, one row per atomic rule with its parameter, enforcement point and whether it is automatable. Use when a process analysis needs to go deeper than narrative, when someone asks for decision logic, thresholds, exception scenarios, approval criteria, customer-specific rules, mappings or validation requirements, when a redesign or build team needs a consumable rule set, or when asked about "tribal knowledge", undocumented workarounds, recurring exceptions or rework drivers in a documented process.
metadata:
  argument-hint: "[path to the SOP document or an already-extracted corpus folder]"
---

# SOP rules register — conduct guide

A process analysis written as narrative tells a reader what the process *is*. A rules
register tells a build team what to *implement*. They are different artefacts and the
second is not a longer version of the first.

The failure this skill exists to prevent: a process report that says "special account
rules apply to Sobeys, Fed-Coop and GFS" when the source actually says the Fed-Coop rule
keys on payer number 1778246, a six-digit PO gets an automatic `CR.REQ` prefix, and mixed
ice-cream-and-retail backups on account 5230470 post to 5260744 instead. The first is a
finding. The second is a specification.

---

## Step 0 — Source integrity gate

**Do this before anything else, and report the result even when it is clean.**

Run the extractor's declared-versus-present reconciliation. A container declares its
embedded objects in its `.rels`; a truncated or partially synced file will still list
objects it no longer physically holds.

```
python ../deep-extract/scripts/deep_extract.py "<SOURCE>" -o <OUTDIR>
```

Read the `Embedded objects (N)` table in the output markdown. Any row reading
`MISSING (truncated file)` is a hole in the evidence base.

State coverage as a fraction on every artefact you produce:

> Coverage: 30 of 42 declared embedded objects recovered (71%). One further object is
> ~31% complete. Absent: … Re-request the intact source before treating this register
> as complete.

Never present a partial extraction as a complete one. An undeclared gap is the single
most damaging defect in this class of work, because a reader has no way to detect it.

---

## Step 1 — Extract the full tree

Use the `deep-extract` skill. Do not settle for body text.

These corpora characteristically hide their content one to four levels down:
outer `.docx` → `oleObject.bin` → `.msg` email → attached `.docx` / `.pptx`. On the
Nestlé CA10 worked example the single most valuable file — a nine-column scenario
decision matrix — sat at depth 4 inside an embedded training email.

Extract **everything**, including:

- embedded `.msg` emails and their own attachments
- embedded workbooks, including hidden sheets, dropdown validation lists and comment columns
- training decks
- headers, footers, footnotes, comments, tracked changes
- document properties — revision count and editing time show which procedures churn

If a previous run already produced a corpus folder, reuse it rather than re-extracting.

---

## Step 2 — Mine candidate statements

Do not read the corpus into context and hunt by eye. A single SOP tree runs to
megabytes; you will miss most of it and will not know which parts you missed.

```
python scripts/mine_rules.py "<CORPUS>.md" [more corpora...] -o <OUTDIR>/rules-mining
```

Outputs:

| file | what |
|---|---|
| `rule_candidates.csv` | one row per deduplicated candidate, with source document and line |
| `rule_candidates.md` | the same, grouped by category, for reading |
| `mining_summary.md` | counts by category, by parameter type, by source document |

The miner classifies against nine families — threshold, conditional, obligation,
approval, exception, mapping, account_specific, timing_sla, tribal — and lifts literal
parameters (money, counts, order types, billing blocks, account numbers, transaction
codes, statuses) out of each statement.

It decides nothing. Splitting compound statements, resolving contradictions and judging
what a rule means are your job.

---

## Step 3 — Build the Business Rules Register

One row per **atomic** rule. Split compound statements. Never carry a rule as prose.

| field | content |
|---|---|
| `rule_id` | `BR-001` onwards |
| `category` | Threshold / Approval / Routing / Validation / Mapping / Exception / Data format / Timing |
| `trigger` | the condition that makes the rule apply |
| `rule` | the obligation, as a single testable statement |
| `parameter` | the literal value — `50,000 CAD`, `$150`, `10 cases`, `12 characters`, `08`, `5260744` |
| `scope` | All / order type / account / BU / market / product category |
| `enforced_by` | SAP automatic · SAP configurable · Manual, processor memory · Manual, documented |
| `on_violation` | what actually happens — EDI failure, rework, financial misposting, or none stated |
| `source` | document name plus section |
| `confidence` | explicit in source / inferred / contradicted elsewhere |
| `automatable` | Yes, deterministic · Yes, with master data · No, judgement |

`enforced_by` and `automatable` are what make the register usable in solution design.
They separate rules a rules engine can hold from rules that need a human, and they
surface contradictions before build rather than during UAT.

Expect roughly 120–180 rows from a mature single-process SOP tree.

### Then derive four tables from the register

- **Threshold register** — every number in the process, with its unit and its owner
- **Approval matrix** — value band × approver role × system of record × SLA × escalation path
- **Account exception register** — one row per named account, carrying all its deviations
- **Field mapping table** — source field to target field, with transformation and length limits

---

## Step 4 — Build the Tribal Knowledge Register

Split it in two. Do not blend them: the second half is a fieldwork request, not a finding.

### 4a — Documented tribal knowledge

Extractable now. Six signals:

| signal | what it yields |
|---|---|
| workaround language — "action crafted is…", "in this case we can use…" | unofficial workarounds already written down |
| verbal-authority markers — "this was aligned with the team lead" | rules with no policy backing |
| backup-person caveats — "if X is not around, Y takes over, however he may not be familiar…" | the real resilience gap behind a named-person risk |
| embedded email threads | live exception negotiation, account by account |
| training material | what new joiners are actually taught, against what the SOP says |
| workbook artefacts — dropdowns, conditional formatting, hidden sheets, comment columns | the de facto taxonomy and the informal detection logic |

Fields: `tk_id`, `type` (workaround / undocumented rule / known defect / account nuance /
resilience gap), `statement`, `why it exists`, `official?` (policy-backed / verbally
agreed / no basis stated), `risk if lost`, `source`.

Document metadata is evidence. A procedure at revision 27 with 1,570 minutes of editing
time is a contested document; say so.

### 4b — Undocumented tribal knowledge

Not obtainable from documents at any depth. State this plainly rather than inferring it,
and convert it into a named request.

| question | required source |
|---|---|
| which exceptions recur most often | change logs, transaction modification counts, mailbox volumes |
| what drives rework | process mining over the real event log |
| which documented rules are actually ignored | conformance check: mined reality against this register |
| workarounds never written down | 3–5 structured practitioner interviews across the roles |

Recommend triangulating three sources — SOP corpus, event log, practitioners. The
register is the cheapest of the three and should run first, because it sets the
interview agenda.

---

## Step 5 — Render

Follow whatever artefact convention the engagement already uses. If none, produce the
register as a spreadsheet and a short HTML page carrying the four derived tables and the
coverage statement.

---

## Guardrails

1. **Every row cites its source document and section.** A rule with no citation is a guess.
2. **Never invent a parameter.** If the source says "large number of cases" and gives no
   number, the `parameter` field reads `not specified in source` — that absence is itself
   a finding worth surfacing.
3. **Declare coverage on every artefact.** See Step 0.
4. **Record contradictions, do not silently resolve them.** Where two documents disagree,
   both rows stay and `confidence` reads `contradicted elsewhere`.
5. **No benefit percentages.** Cycle-time savings, straight-through-processing rates and
   FTE reductions belong to a business case built from client volumetrics. An SOP corpus
   contains none of that; asserting it from a rules register is fabrication.
6. **Keep documented and undocumented tribal knowledge apart.** Blending them lets an
   inference pass as an observation.
7. **Preserve the source's own wording in the `rule` field** where it is already testable.
   Paraphrase costs precision, and precision is the whole point of this artefact.

---

## Worked example

`reference/nestle-ca10-rr.md` records the Nestlé Canada CA10 Returns & Refusals run:
the source-integrity finding, the mining counts, the sixteen-rule spot check against an
earlier narrative-only report, and the reply drafted for the reviewer who asked for
this depth in the first place.
