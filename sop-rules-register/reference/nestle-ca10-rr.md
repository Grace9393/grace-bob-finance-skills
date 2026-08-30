# CA10 R&R — Deep Extraction Spec (response to Tejasvi Manocha feedback)

**Purpose:** turn the two feedback points into a buildable extraction schema.
**Applies to:** `nestl-canada-returns-refusals-full-process-analysis-...html` and any
re-run of the SOP Analysis over `OG_NBS Manila_O2C_CA_Returns and Refusals 1.docx`.
**Evidence base:** `C:\Users\GRACEPAN\Box\#Grace\ClientZero\NAR_Nestle\_extracted\`

---

## 1 · Feasibility verdict

| Ask | Verdict | Constraint |
|---|---|---|
| Deeper decision logic, thresholds, exception scenarios, approval criteria, customer rules, mappings, validation requirements | **Feasible now** | Output schema, not extraction capability. Material is already on disk. |
| Tribal knowledge — recurring exceptions, account nuances, rework drivers, unofficial workarounds | **Feasible for the documented share (~60–70%)** | Frequency and "what people actually do" need transaction data or interviews. |
| Either, at full depth | **Blocked at 71% of source** | Source `.docx` is truncated; 12 of 42 embedded objects are physically absent. |

### What the corpus holds that the current report does not carry

Counted across the extracted corpus (body plus 30 recovered embedded objects):

| Signal | Count |
|---|---|
| Unique `Note:` / `NOTE:` rule statements | 48 |
| Unique conditional statements (`If` / `When` / `In case` / `Once` / `Should`) | 101 |
| Modal obligation statements (`must` / `cannot` / `is required` / `not allowed`) | 18 |
| Distinct monetary thresholds | $100, $150, $1,000, $1,500, 50,000 CAD |

Spot check — 14 of 16 highly specific source rules are **absent** from the current
analysis report:

| Source rule | In report |
|---|---|
| Use account **5260744** when the backup for account **5230470** mixes Ice Cream with pizza/retail | no |
| The Fed-Coop rule applies only when the payer number is **1778246** | no |
| A six-digit PO is auto-prefixed with **`CR.REQ`** by the file | no |
| Overage-kept PO must carry a unique indicator, format `1234-A` | no |
| Carrier claim: FTL threshold differs from LTL; **max 10 cases** on the salvageable branch; above 10 cases moves to non-salvageable | no |
| Vitality products damaged by leaking — **no carrier claim even over $100**, destroy only | no |
| All **NHS** products must be returned | no |
| Sold-to marked for deletion — **proceed anyway**, disregard the warning (aligned with the CoS Claims Analyst Team Lead) | no |
| External Reference prevails over the PO copy, because UDM/SAP caps the field at 12 characters | partial |
| Subsequent-document rule: block and attach on the **subsequent** document only, not the initial one | no |
| ZRR alone takes no billing block; ZCRQ receives 08 automatically; ZDRQ needs 09 entered manually | partial |
| At or above 50,000 CAD on a ZRR with a subsequent document, **both** documents need market unblocking | no |
| Ice cream and pizza orders validate on the **net** amount, without tax | partial |
| A ZCRQ raised by a Claims Analyst through the C&D Cockpit may mismatch the deduction amount — proceed | no |
| Do not close or reassign the activity or case ID until the note is billed **and** an accounting document exists | no |
| Manual Draft Posting SLA is **2 business days** — the report shows a flat 48 hours for everything | no |

### The richest unread source

`Returns_ Refusals and Credits Scenarios.docx` — 9 pages, 2,164 words, revision 27,
authored by Nestlé Canada Customer Service, last modified by Varsha Baichoo.
It sits at **depth 4**: master `.docx` → `oleObject2.bin` →
`RE_ Refresher Training for OSD.msg` → attachment.

It is a nine-column scenario matrix:

`Scenario | Steps to Validate | Transaction | PO# | Reason Code | Notes | Authorization tab in OSD tool | Carrier Claim? | Reason in OSD Tool`

The report's §3 matrix has five columns. It drops *Steps to Validate*, *PO#*,
*Notes* and *Reason in OSD Tool* — which is where the validation criteria, the
format conventions and the exception handling live.

Unread at the same depth: `OS_D TRAINING.pptx`, `117-02 How to Process OSD.docx`,
`OSD process for CoS and CoC.docx`, and three embedded Excel workbooks.

---

## 2 · Source integrity — fix before extracting deeper

`OG_NBS Manila_O2C_CA_Returns and Refusals 1.docx` is **truncated**: 64,903,660 bytes,
ZIP central directory absent, Word cannot open it at all.

| | Count |
|---|---|
| Embedded objects declared | 42 |
| Fully recovered | 29 |
| Partially recovered | 1 — `Microsoft_Word_Document24.docx`, about 31% |
| Physically absent | 12 |

Absent: `oleObject5`–`oleObject10`, `Microsoft_Word_Document25 / 28 / 29 / 30`,
`Microsoft_Excel_Worksheet26 / 27`. `Worksheet27` is the workbook attached to the
**Error in Materials** section — the material-error mapping table is one of the
missing files.

**Action:** re-request the intact source from NBS Manila before the deeper run.
Confirm at the same time whether `CA Returns and Refusals – ALL.docx` — the filename
the report cites — is a different and complete file.

---

## 3 · Output schema to add — Business Rules Register

One row per **atomic** rule. Split compound statements; never carry a rule as prose.
Expected yield from the Word corpus alone: **120–180 rows**.

| Field | Content |
|---|---|
| `rule_id` | `BR-001` onwards |
| `category` | Threshold / Approval / Routing / Validation / Mapping / Exception / Data format / Timing |
| `trigger` | The condition that makes the rule apply |
| `rule` | The obligation, as a single testable statement |
| `parameter` | The literal value — `50,000 CAD`, `$150`, `10 cases`, `12 characters`, `08`, `5260744` |
| `scope` | All / order type / account / BU / market / product category |
| `enforced_by` | SAP automatic · SAP configurable · Manual, processor memory · Manual, documented |
| `on_violation` | What actually happens — EDI failure, rework, financial misposting, or none stated |
| `source` | Document name plus section |
| `confidence` | Explicit in source / inferred / contradicted elsewhere |
| `automatable` | Yes, deterministic · Yes, with master data · No, judgement |

The last two columns are what makes the register usable in solution design. They
separate rules a rules engine can hold from rules that need a human, and they surface
contradictions before build rather than during UAT.

Add these as separate tables:

- **Threshold register** — every number in the process, with its unit and its owner
- **Approval matrix** — value band × approver role × system of record × SLA × escalation
- **Account exception register** — one row per named account, carrying all its deviations
- **Field mapping table** — source field to SAP field, with transformation and length limits

---

## 4 · Output schema to add — Tribal Knowledge Register

Separate the two kinds. Do not blend them: the second is a fieldwork request, not a
finding.

### 4a · Documented tribal knowledge — extractable now

Six signals to mine:

| Signal | Where | What it yields |
|---|---|---|
| Explicit workaround language — "Action crafted is…", "in this case we can use…" | SOP body | Unofficial workarounds already written down |
| Verbal-authority markers — "this was aligned with the CoS Claims Analyst Team Lead" | SOP body | Rules with no policy backing |
| Backup-person caveats — "If Habib is not around, Inas should take charge, however he may not be familiar…" | SOP body | The real resilience gap behind the named-person risk |
| Four embedded `.msg` threads | `sub/` | Live exception negotiation — Fed-Coop urgent PO, GFS blocked orders and debit memo, ZCRQ condition-type alignment, OSD refresher training |
| Training material — `OS_D TRAINING.pptx`, `117-02 How to Process OSD.docx` | depth 4 | What new joiners are actually taught, against what the SOP says |
| Excel artefacts — dropdown validation lists, conditional-formatting rules, hidden sheets, comment columns | three embedded workbooks | The de facto taxonomy and the duplicate-detection logic |

Register fields: `tk_id`, `type` (workaround / undocumented rule / known defect /
account nuance / resilience gap), `statement`, `why it exists`, `official?`
(policy-backed / verbally agreed / no basis stated), `risk if lost`, `source`.

Metadata is evidence too. Revision counts and editing time per SOP show which
procedures churn: `Returns_ Refusals and Credits Scenarios.docx` stands at revision 27
with 1,570 minutes of editing, which marks it as a contested document.

### 4b · Undocumented tribal knowledge — needs a second source

Not obtainable from documents at any depth. State this plainly rather than inferring it.

| Question | Required source |
|---|---|
| Which exceptions recur most often | SAP change logs, VA02 modification counts, OS&D mailbox volumes |
| What drives rework | Process mining — Celonis or MyInvenio — over the real event log |
| Which documented rules are actually ignored | Conformance check: mined reality against this register |
| Workarounds never written down | Three to five structured practitioner interviews — two processors, one validator, one CSA, one team lead |

Triangulate three sources: the **SOP corpus** (this register), the **event log**
(process mining) and the **practitioners** (interviews). Any one alone gives a partial
picture. The register is the cheapest of the three and should run first, because it
sets the interview agenda.

---

## 5 · Sequence

| # | Step | Blocks |
|---|---|---|
| 1 | Re-request the intact source `.docx` from NBS Manila | everything below runs at 71% until this lands |
| 2 | Extract the four `.msg` threads, three Excel workbooks and the training deck — currently out of scope | 4a |
| 3 | Build the Business Rules Register from the full corpus | §3 |
| 4 | Build the Documented Tribal Knowledge Register | §4a |
| 5 | Rebuild §3 of the report from the nine-column scenario matrix, not the five-column summary | report fix |
| 6 | Declare the twelve missing objects on the page | credibility |
| 7 | Scope the interviews and the process-mining run from what §4b leaves open | 4b |

Steps 3 to 6 need no new tooling and no new client input.

---

## 6 · Draft reply to Tejasvi

> Thanks Tejasvi — both points are actionable, and we have run them down against the source.
>
> On deeper rule extraction: yes, and further than the current output suggests. The corpus
> carries 48 distinct "Note" rules, 101 conditional statements and five monetary thresholds
> ($100, $150, $1,000, $1,500 and 50,000 CAD). We also found a nine-column
> Returns/Refusals/Credits scenario matrix nested four levels deep inside an embedded
> training email — it carries the validation steps, PO format conventions and OS&D reason
> mappings that the current summary compresses into five columns. Concrete examples now
> missing: the account substitution 5230470 to 5260744 for mixed ice cream and retail
> backups, the Fed-Coop rule keying on payer 1778246, the automatic CR.REQ prefix on
> six-digit POs, and a carrier-claim rule that carries a case-count and a shipment-mode
> condition beyond the $150 threshold. The next version adds a Business Rules Register —
> one row per atomic rule with its parameter, scope, enforcement point and whether it is
> automatable — plus separate threshold, approval-matrix, account-exception and
> field-mapping tables. That is the artefact a redesign or a build team can consume directly.
>
> On tribal knowledge: partly, and we should be precise about which part. The documented
> share is extractable. The SOP contains explicit workarounds, rules justified only as
> "aligned with the team lead", and backup-person caveats that name the real resilience
> gaps. Four embedded email threads capture live exception handling on Fed-Coop, GFS and
> ZCRQ condition types, and a training deck shows what new joiners are actually taught.
> None of that has been read yet — email and Excel were scoped out of the first pass. We
> will bring them in.
>
> What documents cannot give us is frequency: which exceptions recur, what drives rework,
> and which rules are quietly ignored. That needs the event log or the people. We suggest
> triangulating three sources — the SOP register first because it is cheapest and it sets
> the agenda, then process mining on the SAP event log, then a short round of practitioner
> interviews to close what remains.
>
> One caveat worth flagging: the source file we were given is truncated. Twelve of its
> forty-two embedded objects are physically absent, including the material-error mapping
> workbook. Everything above runs at roughly 70% coverage until we have an intact copy.
> Could you help us re-request it from NBS Manila?


---

## 7 - Actual mining run (2026-08-25)

Input: the depth-4 extraction of `OG_NBS Manila_O2C_CA_Returns and Refusals 1.docx`,
covering 30 of 42 declared embedded objects.

```
python scripts/mine_rules.py "<corpus>.md" -o rules-mining
```

# Mining summary

- corpus files: 1
- raw candidate statements: 1158
- after deduplication: 815
- miner version: 1.0.0

## By category (primary hit)

| category | count |
|---|---|
| mapping | 301 |
| threshold | 140 |
| account_specific | 127 |
| conditional | 119 |
| exception | 47 |
| obligation | 37 |
| tribal | 25 |
| approval | 15 |
| timing_sla | 4 |

## By parameter type

| parameter | statements |
|---|---|
| order_type | 158 |
| count | 38 |
| txn_code | 26 |
| money | 22 |
| account_no | 9 |
| billing_block | 5 |
| status | 1 |

## By source document (top 30)

| source | count |
|---|---|
| Microsoft_Excel_Worksheet.xlsx | 142 |
| OG_NBS Manila_O2C_CA_Returns and Refusals 1.docx | 120 |
| Microsoft_Word_Document3.docx | 79 |
| Returns, Refusals and Credits Scenarios.docx | 65 |
| Microsoft_Word_Document.docx | 47 |
| Microsoft_Word_Document14.docx | 38 |
| Microsoft_Word_Document9.docx | 34 |
| Microsoft_Word_Document15.docx | 21 |
| Microsoft_Excel_Worksheet19.xlsx | 21 |
| Microsoft_Excel_Worksheet20.xlsx | 20 |
| Microsoft_Word_Document10.docx | 20 |
| Microsoft_Word_Document5.docx | 18 |
| Microsoft_Word_Document1.docx | 17 |
| Microsoft_Word_Document21.docx | 17 |
| Microsoft_Word_Document22.docx | 17 |
| Microsoft_Word_Document24.docx | 15 |
| Microsoft_Word_Document2.docx | 14 |
| Microsoft_Word_Document7.docx | 13 |
| Microsoft_Word_Document13.docx | 13 |
| Microsoft_Word_Document4.docx | 12 |
| OSD process for CoS and CoC.docx | 12 |
| Microsoft_Word_Document6.docx | 11 |
| Microsoft_Word_Document11.docx | 10 |
| RE  Condition Type Alignment (ZCRQ processing CA10).msg | 10 |
| Microsoft_Word_Document8.docx | 7 |
| Microsoft_Word_Document16.docx | 6 |
| RE_ Refresher Training for OSD.msg | 5 |
| Microsoft_Word_Document12.docx | 3 |
| Microsoft_Word_Document17.docx | 3 |
| Microsoft_Word_Document18.docx | 2 |


The register built from these 815 candidates is expected to land at 120-180 atomic rules
after compound statements are split and workbook row noise is discarded.
