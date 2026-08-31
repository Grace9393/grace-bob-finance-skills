# Target Operating Model — target-state architecture for the finance function

> **Not a "blueprint."** In this practice a *blueprint* is the house use-case deliverable
> (narrative → 4 pain points → 3 agents → user benefits → 4 business benefits), owned by the
> Blueprint Accelerator. This document defines the **target operating model (TOM)** — the
> function-level architecture. See `house-style-and-blueprint-contract.md` §1.

The TOM is the client's answer to *"what does our finance function look like when this is done,
and why that shape?"* It is not a system diagram and not an org chart. It is the seven layers
below, made consistent with each other and traceable to stated design principles.

A TOM is complete when someone who was not in the room can read it and correctly predict what the
roadmap will contain.

---

## 1. The seven layers

| # | Layer | The question it answers | Minimum artifact |
|---|---|---|---|
| 1 | Value proposition | What does finance exist to deliver for this business, and what is the split between stewardship, operations and business partnering? | Statement of role + the target effort mix (e.g. 30/40/30 → 20/30/50) |
| 2 | Service delivery model | Who performs each process, and where? | Delivery model map (§3) per L2 process |
| 3 | Process architecture | What are the end-to-end processes, their hand-offs and their standards? | L1–L3 taxonomy (§2) + hand-off map per E2E flow |
| 4 | Data & technology | What is the system landscape, the data model, and the single source of truth for each object? | Application map + data domain ownership table |
| 5 | Organization & talent | What roles, skills, spans and layers deliver the model? | Role architecture + capability/skill gaps |
| 6 | Governance & policy | Which decisions are made where, under which policies and controls? | Decision rights (RACI at L2) + policy inventory |
| 7 | Performance management | How is finance itself measured and steered? | KPI tree + reporting cadence |

**Consistency tests** — run these before showing a TOM. Each one catches a common defect:

- Every L2 process in layer 3 has exactly one delivery-model assignment in layer 2.
- Every data object with more than one system of entry in layer 4 has a named owner in layer 6.
- Every effort-mix shift claimed in layer 1 is reflected by role changes in layer 5. Claiming
  "more business partnering" with an unchanged role architecture is the single most common
  TOM defect.
- Every KPI in layer 7 has a source system in layer 4. KPIs with no feasible data source are the
  second most common.

---

## 2. Finance process taxonomy

Anchor to APQC's Process Classification Framework (PCF) so benchmark data joins cleanly.
"Manage financial resources" is **category 9.0** in the PCF 7.x cross-industry framework and
**8.0** in several industry and later variants — always state the PCF version you used, and
verify the numbering against that version's PDF before printing hierarchy IDs on a client page.

Working L1/L2 structure for assessments (consulting E2E names in brackets, since clients use them):

**A. Plan and analyse** *(Plan-to-Perform / FP&A)*
- A1 Strategic and long-range planning
- A2 Budgeting, forecasting and target setting
- A3 Management reporting and analysis
- A4 Cost and profitability management
- A5 Business partnering and decision support

**B. Record and report** *(Record-to-Report)*
- B1 General accounting and journal processing
- B2 Intercompany accounting
- B3 Fixed assets and lease accounting
- B4 Reconciliations and close
- B5 Consolidation and statutory/external reporting
- B6 Financial control and compliance (incl. SOX/ICFR)

**C. Source and pay** *(Procure-to-Pay / Source-to-Pay)*
- C1 Supplier master data
- C2 Requisition, PO and receipt
- C3 Invoice processing and matching
- C4 Payments and disbursement control
- C5 Travel and expense
- C6 Supplier enquiry and dispute

**D. Sell and collect** *(Order-to-Cash / Invoice-to-Cash)*
- D1 Customer master data and credit
- D2 Order management and pricing control
- D3 Billing and invoicing
- D4 Collections and dunning
- D5 Cash application
- D6 Disputes, deductions and write-offs
> For a deep O2C engagement, switch to the `ar-diagnostic` skill (06) — it carries the full
> KPI baseline script and AR-specific taxonomy.

**E. Manage cash and risk** *(Treasury)*
- E1 Cash and liquidity management
- E2 Banking, in-house bank and payment factory
- E3 Debt, investment and FX/commodity risk
- E4 Financial risk policy and hedge accounting

**F. Manage tax** — F1 direct tax · F2 indirect tax/VAT/e-invoicing compliance · F3 transfer pricing · F4 tax reporting and provisioning

**G. Pay people** *(Hire-to-Retire finance scope)* — G1 payroll accounting · G2 payroll controls and reconciliation

**H. Steer the function** — H1 finance strategy and transformation · H2 finance systems and data ownership · H3 finance talent · H4 internal audit (where in scope)

Decompose to **L3** only for processes in scope. L4/L5 belongs in design, not assessment —
assessments that decompose everything to task level burn the timeline and produce no decisions.

---

## 3. Service delivery model options

Assign every L2 process to one of these. The trade-off column is what the client will argue about.

| Model | Best for | Trade-off you must state |
|---|---|---|
| **Retained / in-country** | Judgement-heavy, statutory-bound, relationship-critical work | Highest unit cost; hardest to standardise; the default resting place for work nobody wants to move |
| **Centre of Excellence (CoE)** | Scarce expertise applied across units — tax, treasury, technical accounting, FP&A modelling | Only works with genuine demand management; otherwise becomes a queue |
| **Shared Service Centre (SSC)** | High-volume, rules-based, standardisable transactions | Requires process standardisation *before* the lift; lifting chaos yields cheaper chaos |
| **Global Business Services (GBS)** | Multi-function scale, E2E process ownership across finance/HR/procurement | Governance load; needs real E2E process owners with authority, not coordinators |
| **Outsourced (BPO)** | Commoditised volume, labour arbitrage, access to provider platforms | Contract becomes the operating model; change costs money; retained-org capability must survive |
| **Automated / touchless** | Structured, high-volume, exception-light steps | Automating a broken process locks the defect in; exception design *is* the design |
| **Agentic / AI-assisted** | Judgement-adjacent work with reviewable output — variance narratives, reconciliation matching, dunning drafts, document extraction | Needs evidence, audit trail and a human decision point; treat output as a draft for a named approver, never as a posted action |

**Split criteria** — apply consistently rather than case by case: transaction volume · degree of
judgement · statutory/regulatory constraint · language and time-zone need · data sensitivity ·
system access · variability of input · consequence of error.

---

## 4. Maturity model (5 levels × 5 lenses)

Score every in-scope capability on all five lenses. This is what `ft_analyze.py score` consumes,
and the lens vocabulary is shared with `pain-point-taxonomy.md` so findings and scores reconcile.

| Level | Name | Generic descriptor |
|---|---|---|
| 1 | Ad hoc | Undefined and person-dependent; outcomes vary by who does the work |
| 2 | Repeatable | Locally documented; consistent within a team but not across teams or entities |
| 3 | Defined | Standardised and documented globally; exceptions are visible and managed |
| 4 | Managed | Measured against targets; root causes acted on; performance is stable and predictable |
| 5 | Optimised | Continuously improved; largely touchless; capacity redirected to judgement work |

Lens-specific anchors (what Level 3 and Level 5 look like per lens):

| Lens | Level 3 looks like | Level 5 looks like |
|---|---|---|
| **People** | Defined roles, documented procedures, cross-training within team | Skills matched to judgement work; capacity actively redeployed; low key-person risk |
| **Policy** | Global policy exists and is current; exceptions logged | Policy enforced in-system by design; exception volume itself is a managed KPI |
| **Process** | Single standard process with managed variants; hand-offs defined | Touchless straight-through for the standard path; variants justified and few |
| **Data** | Agreed definitions, one system of record per object, known quality issues | Quality measured at source with owners; issues prevented, not corrected downstream |
| **Technology** | Fit-for-purpose core with integrated main flows | Integrated, low manual intervention, changes deployed without heroics |

Scoring discipline: a level is only awarded if the client can **evidence** it (document, system
screenshot, metric). Self-reported maturity runs about a level high; say so when you present.

---

## 5. Design principles

Agree 5–8 before designing anything; they are the tie-breakers that keep the TOM coherent
when trade-offs bite. Choose from — and force explicit ranking of — principles like:

- Standard before automation; automate only what is standard.
- One version of the truth; single system of entry per data object.
- Global process, local statutory variation only where legally required.
- Design for exception prevention, not exception handling.
- Self-service by default; finance handles exceptions, not requests.
- Controls automated and preventive, not manual and detective.
- Cloud/vendor-standard first; customise only against a quantified business case.
- Judgement work retained; rules-based work centralised or automated.
- Skills and capacity released are redeployed, not simply removed. *(State the truth here — if
  the mandate is headcount reduction, say so; a false principle poisons the change programme.)*

Record for each: the principle, why this client, and what it means the client is choosing
*against*. A principle with no cost is not a principle.

---

## 6. TOM one-pager

The single page that survives the engagement. Structure:

1. **Ambition** — one sentence on finance's role, plus the effort-mix shift (from → to).
2. **Design principles** — the ranked 5–8.
3. **The model** — delivery-model map: L2 processes down, delivery models across, today vs target.
4. **What changes** — the 6–10 headline shifts, each tagged with its lens.
5. **What it takes** — investment envelope, timeline, critical dependencies.
6. **What it delivers** — benefit summary by category (never one blended number — see
   `roadmap-and-business-case.md` §2).

---

## 7. Failure modes

- **Benchmark-driven TOM.** Designing to reach a quartile rather than to serve the business.
  Benchmarks size the gap; strategy chooses the shape.
- **Technology-first TOM.** Layers 4 and 5 designed, layers 1, 2, 6, 7 left implicit. The
  programme then delivers a system and no change in how finance works.
- **Copy of the last client.** Reference models accelerate; they do not decide. Every layer must
  be argued from this client's principles, footprint and constraints.
- **Unowned target state.** No named executive per layer means no decisions between workshops.
- **Silent standardisation assumption.** Assuming entities will adopt a standard process without
  testing statutory, ERP and contractual constraints — the usual reason Wave 2 slips.

---

## Sources
- APQC Process Classification Framework, cross-industry (category "Manage financial resources"),
  https://www.apqc.org/process-frameworks — verify category numbering against the version in use.
- APQC industry-specific PCFs, https://www.apqc.org/process-frameworks/industry-specific-process-frameworks
- Delivery-model, maturity-level and design-principle content in §3–§5 is practitioner-standard
  consulting structure, not a cited external framework — treated as `directional` under the
  citation rules in `benchmark-library.md` §0 and never presented as third-party research.
