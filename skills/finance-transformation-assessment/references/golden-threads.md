# Golden Threads — the IBM Global Finance Transformation process spine

A **golden thread** is one end-to-end finance process decomposed to the step at which an AI use
case can be defined. Three threads are built today, numbered 1–3, covering **220 steps**:

| # | Thread | Sections | Steps | Prototype source |
|---|---|---|---|---|
| 1 | **RTR** — Record-to-Report | 12 | 73 | `ibm-record-to-report-full.html` |
| 2 | **S2P** — Source-to-Pay | 16 | 59 | `source-to-pay.html` |
| 3 | **OTC** — Order-to-Cash | 11 | 88 | `IBM_OTC_Golden_Thread_AI_Use_Cases.md`, `order-to-cash.html`, `OTC-3.7-Collections.md` |

Sources live in `C:\Users\GRACEPAN\Box\#Grace\[INTERNAL]\Studio`. The machine-readable taxonomy —
every step with its section, thread, process-area mapping and assessment mapping — is
`assets/golden-thread-taxonomy.csv`, generated from the prototype sources rather than retyped.

Numbering is `<thread>.<section>.<step>`: `1.8.3` is RTR → Account Reconciliation → Review and
Approve Account Reconciliations. **Use these identifiers verbatim.** They are how the prototype,
the client and every downstream artifact refer to the same work.

---

## 1. Section maps

**RTR (1.x)** — 1.1 Accounting Policy Maintenance (3) · 1.2 GL and Reporting System Maintenance (5) ·
1.3 Journal Entry Processing (4) · 1.4 Cost and Inventory Accounting (8) · 1.5 Fixed Assets
Accounting (8) · 1.6 Project Accounting (6) · 1.7 Intercompany Processing and Settlements (5) ·
1.8 Account Reconciliation (5) · 1.9 Period-End Close and Consolidation (8) · 1.10 Tax Accounting
and Compliance (7) · 1.11 Financial Planning and Analysis (8) · 1.12 Statutory and External
Reporting (6)

**S2P (2.x)** — 2.1 Procurement Strategy, Policy and Governance (6) · 2.2 Category Management (5) ·
2.3 Sourcing and Supplier Selection (4) · 2.4 Contract Management (5) · 2.5 Supplier Management (2) ·
2.6 Catalog Management (2) · 2.7 Requisition and Purchase Order (4) · 2.8 Goods and Service Receipt
(3) · 2.9 Invoice Document Management (4) · 2.10 Invoice Validation and Approval (2) · 2.11 Payments
(6) · 2.12 Vendor and GR/IR Reconciliation (3) · 2.13 Audit, Duplicate and Recovery (3) ·
2.14 Travel and Expense (4) · 2.15 Helpdesk and Query Management (3) · 2.16 Reporting and Cash
Forecasting (3)

**OTC (3.x)** — 3.1 Master Data Management (8) · 3.2 Credit Management (8) · 3.3 Order/Contract
Management (10) · 3.4 Order Fulfillment (6) · 3.5 Billing & Invoicing (11) · 3.6 Customer / Product
Support (6) · 3.7 Collections (11) · 3.8 Dispute & Deduction Management (9) · 3.9 Cash Applications
(11) · 3.10 Adjustment Credit Admin (6) · 3.11 Reporting & Analysis (2)

Query the CSV rather than this list when you need step detail:

```
python scripts/ft_golden_thread.py list --thread RTR --section 1.8
python scripts/ft_golden_thread.py list --area OTC
```

---

## 2. The modal — what sits on every step

Each step carries one **AI use case modal**, and every modal has the same shape:

| Field | Content |
|---|---|
| AI use case | The named use case, e.g. "Automated CMD Creation & Validation" |
| Key personas | Named personas from the thread's persona set (§4) |
| Journey narrative | **Three paragraphs**: current state and its cost → the agents step in → end state for the named persona |
| Modal description | Two or three sentences describing the solution |
| Pain points addressed | Typically **3** |
| Business benefits | **4** |
| User benefits | One line per persona role, phrased as what that person now does differently |
| Agents involved | Typically **3**, named as roles ("SKU Product Mapping Agent"), never products |

This is the same artifact as the house blueprint — with two structural deltas that matter.

---

## 3. Modal → blueprint conversion (the deltas)

The blueprint contract in `house-style-and-blueprint-contract.md` §2 enforces exact counts. A
golden-thread modal does **not** satisfy it as-is:

| Element | Modal (as built) | Blueprint contract | Action |
|---|---|---|---|
| Narrative | 3 paragraphs, current → agents → end state | 3 paragraphs, same sequence | ✅ maps directly |
| Business benefits | 4 | exactly 4 | ✅ maps directly |
| Agents | 3, each with a named human approver in the narrative | exactly 3, each with an explicit `human_review` field | ⚠️ lift the approver out of the narrative into `human_review` — do not leave it implicit |
| Pain points | usually 3 | **exactly 4** | ⚠️ a fourth must come from the assessment register, not from invention |
| User benefits | 1 line per role | **exactly 3 per role** | ⚠️ expand from the register, or reduce the number of roles |

**Never pad to hit a count.** Where the register cannot supply a fourth evidenced pain point or a
third benefit for a role, raise a checkpoint flag saying what is missing. That is the contract's
explicit instruction and the rule a model is most likely to break while trying to be helpful.

This is precisely why the assessment runs first: Phase 3 produces evidenced, quantified,
root-caused pain points tagged by process area and dimension, which is exactly the input the
conversion needs. Modals drafted without it invent their own pain points.

---

## 4. Persona sets — three of them, not one

| Set | Personas | Source |
|---|---|---|
| **RTR thread** | Avery Chen (Finance Systems Director), Casey O'Neill (GL Accounting Lead), Jordan Alvarez (Technical Accounting Lead), Morgan Patel (Corporate Controller), Priya Desai (Treasury Manager), Quinn Rivera (Finance Data & Systems Owner), Riley Thompson (Financial Operations Manager), Sloane Kim (Consolidation & External Reporting Manager) | `RTR_Documentation_Complete.md` |
| **OTC thread** | Peyton Rao (Head of OTC), Dana Morales (VP OTC / Master Data & Pricing Lead), Eliza Park (Credit Manager), Jamie Foster (Order Management Lead), Reese Okoye (Billing & Invoicing Manager), Malik Chen (Collections Manager), Niko Alvarez (Cash Applications Lead), Theo Grant (OTC Analytics & Reporting Lead); also Omar Vidal, Jules Carter, Mara Santos, Caleb Owens, Aiden Brooks | `IBM_OTC_Golden_Thread_AI_Use_Cases.md` |
| **Blueprint accelerator inventory** | Mara Santos, Devon Park, Priya Iyengar, Hugo Beck, Lena Ostrowski, Cameron Ortiz, Aiko Tanaka, Marco Silva | `blueprint-accelerator/personas/inventory.yaml` |

**These sets are not reconciled.** Only *Mara Santos* appears in more than one, and Dana Morales
carries two different role titles inside the OTC thread itself ("VP of Order-to-Cash" in the
persona list, "Master Data & Pricing Lead" in the 3.1 narratives).

Working rule: **the accelerator inventory is the source of truth for drafted blueprints**
(`house-style-and-blueprint-contract.md` §3). When converting a modal, map the thread persona to an
inventory archetype and raise a `persona_flag` for anyone with no match. Do not silently carry a
thread persona into a blueprint, and do not add one to the inventory without senior review.

---

## 5. From golden thread to agentic app

A modal states *what* the AI use case is. Turning one into a running application uses the six-phase
method in `general-accounting-reporting-FPA-APP.md`, which is worth knowing in full because it is
what a client buys after the assessment:

1. **Cognitive Deconstruction** — atomic thinking step register (each step typed `DET` or `AI`,
   assigned an autonomy zone and a reliability target), business ontology, autonomy zone map,
   human-in-the-loop specification, data products, systems-of-record integration, MCP tool
   register, agent definition register.
2. **Context & Memory Engineering** — context payload per step, memory architecture, audit trace.
3. **Agentic App Engineering** — agent roster, model selection, skills library, MCP tool plan,
   orchestration topology, A2A contracts, guardrails, error handling, observability.
4. **Hardening & Verification** — functional, behavioural, adversarial and domain evals, failure
   mode and fallback testing, HITL validation. *Exit by performance, not completion.*
5. **Agentic Activation** — Wave 1 shadow mode → Wave 2 green-zone activation → Wave 3 full
   activation, each with numeric exit criteria.
6. **Agentic Operations & Evolution** — control tower, eval suite per cycle, pinned model versions,
   human-override analysis feeding improvement, periodic recalibration.

**Autonomy zones** are the governance idea to carry into every conversation:

| Zone | Meaning | Treatment |
|---|---|---|
| **GREEN** | Deterministic, rule-based, ~99.9% reliability | Runs unattended |
| **AMBER** | AI-powered judgement, ~90–95% reliability | Named reviewer, defined validation scope, authority and SLA; every override logged and fed back |
| **RED** | Not automated | Stays human |

All AI steps start AMBER and are promotable to GREEN only when eval baselines mature (97%+ over
several cycles). The worked example runs 8 GREEN / 5 AMBER / 0 RED across 13 atomic steps.

This maps directly onto the delivery-model row **"Agentic / AI-assisted"** in
`target-operating-model.md` §3, and it is the answer to the CFO question *"what stops it going
wrong?"* — zones, named reviewers, SLAs, evals and activation waves, not assurances.

---

## 6. Business case anchors from the OTC thread

The OTC executive summary (88 modals, May 2026) quotes: total annual savings **$8–15M**, cash
acceleration **$5–20M**, implementation cost **$2.5–3.5M**, payback **3–6 months**, ROI
**200–400%**; automation 80–90%, cycle time −40–70%, error rate −85–95%, FTE −25–35%; **DSO −8–15
days**, collection rate +15–20%, bad debt −40–50%. Phasing: Phase 1 (4 mo) 3.1, 3.2, 3.5 · Phase 2
(4 mo) 3.7, 3.9, 3.6 · Phase 3 (4 mo) 3.3, 3.4, 3.8, 3.10 · Phase 4 ongoing 3.11.

**Treat these as a prototype's illustrative case, not as a benchmark.** They carry no client
baseline, no population and no source, so under the citation rules in `benchmark-library.md` §0
they are `directional` — usable to frame a range in discussion, never quotable as a figure on a
client page or in a business case. The RTR document's "Close Cycle Time Improvement: 95%" is the
clearest example: it is not reconcilable with the APQC quartiles (10 days → 5 days is a 50%
improvement, and top quartile is 4.5–5 days), so quoting it would invite exactly the challenge you
cannot answer. Size the client's own case from Phase 2 and Phase 4 of the assessment instead.

---

## 7. Source inventory and its defects

Read this before citing any document in the Studio folder.

**Prototype-faithful (use these):**
- `ibm-record-to-report-full.html` — the RTR app: 12 sections, 73 steps with full modals.
- `source-to-pay.html` — the S2P app: 16 sections, 59 steps.
- `IBM_OTC_Golden_Thread_AI_Use_Cases (1).md` — the OTC capture: correct 88-step structure; 16
  modals transcribed verbatim, the rest titled or marked pending.
- `order-to-cash.html` — OTC section 3.1 only, with full modal data.
- `OTC-3.7-Collections (1).md` — the authoritative 3.7 Collections step names and modals.
- `general-accounting-reporting-FPA-APP.md` — the six-phase agentic app method (APQC PCF 9.3).

**Do not cite as the prototype:**
- `IBM_OTC_AI_UseCases_Complete_88Modals*` — contains **68** modals, not 88, and its step names
  (e.g. 3.7.1 "Collection Strategies", 3.7.2 "Delinquency Prediction & Prevention") do not match
  the prototype's (3.7.2 "Customer Segmentation & Risk Scoring"). Separately generated content.
- `IBM_OTC_MASTER_DOCUMENT_88Modals_FULL_INFORMATION.md` — a **third** and different set of 3.1
  step names ("Master Data Quality Management", "Automated GL Chart Synchronization"). Also
  inconsistent with the prototype.
- `IBM_OTC_AI_UseCases_Complete_42_Modals.*`, `IBM_OTC_Complete_31-88_Full.*`,
  `IBM-OTC-Consolidated-89-Modals.html` — partial or differently-scoped captures; the last claims
  89, not 88.
- `RTR_Documentation_Complete.md` — states the RTR framework has **8** steps and documents 6
  sub-steps. The prototype has **12 sections and 73 steps**. Useful for its persona profiles and
  its six transcribed modals; incomplete as a framework reference.

**32 OTC step titles (sections 3.4, 3.5, 3.6, 3.8) were never captured from the prototype.** They
are marked `pending` in the taxonomy CSV. Recover them from the running prototype before scoping
work in those sections — do not substitute the names from the non-prototype documents, which is
the trap this section exists to prevent.

---

## 8. Scoping an engagement against the threads

1. **Set scope in thread identifiers**, not prose: "RTR 1.7–1.9 and OTC 3.7, 3.9" is auditable;
   "the close and collections" is not.
2. Run `python scripts/ft_golden_thread.py scope 1.7 1.8 1.9 3.7 3.9` for the step list, the
   process-area mapping and the assessment-taxonomy mapping, plus a warning for any section with no
   process area.
3. Map each in-scope section to the assessment taxonomy (`assessment_l2` column) so Phase 2
   benchmarks and Phase 3 pain points attach to the same spine.
4. In Phase 3, tag every register row with its `step` so findings and modals reconcile.
5. In Phase 4, `python scripts/ft_golden_thread.py queue <initiative-backlog.csv>` produces the
   blueprint drafting queue in wave order.

**The S2P gap.** All 59 S2P steps sit outside the blueprint process-area enum — there is no `S2P`
or `P2P` member. S2P scope can be assessed, benchmarked (AP cost per invoice is one of the
best-evidenced metrics in the library) and roadmapped normally, but it **cannot be drafted as a
blueprint** until the enum is extended, which per `AGENTS.md` requires the system prompt, the
validator, the ICA prompt and the benchmark scenarios to change in one commit. Raise it at Phase 1
scoping, not when the drafting queue turns up empty.
