# Reference process flows and diagram definitions

Ready-to-render definitions for the diagrams an assessment needs. Feed the swimlane blocks to the
`swimlane-diagram` skill, the Mermaid blocks to any Mermaid renderer (Artifacts render them
natively), and the layer diagram to `transformation-architecture-diagram`.

**These are reference models.** Redraw every flow against what the client actually does — the
value of a hand-off map is that it shows *their* hand-offs. Use these to structure the interview
and to mark the deltas, never as the finding itself.

---

## 1. Purchase-to-Pay — hand-off map

Lanes are where the work sits; the hand-offs between lanes are where the defects are.

```mermaid
flowchart LR
  subgraph Requester
    A1[Identify need] --> A2[Raise requisition]
  end
  subgraph Procurement
    A2 --> B1[Approve / source] --> B2[Issue PO]
  end
  subgraph Supplier
    B2 --> C1[Deliver goods / services] --> C2[Send invoice]
  end
  subgraph Receiving
    C1 --> D1[Goods receipt]
  end
  subgraph AP
    C2 --> E1[Capture invoice] --> E2{3-way match}
    E2 -- matched --> E3[Post] --> E4[Pay run]
    E2 -- exception --> E5[Exception queue] --> E6[Chase requester / buyer] --> E2
  end
  subgraph Treasury
    E4 --> F1[Execute payment]
  end
```

**Where to look:** invoices arriving with no PO (policy) · goods receipt not entered (process) ·
supplier master duplicates causing match failure (data) · exception queue with no ageing or owner
(process + people) · manual payment proposals (technology).

**Metrics to capture per hand-off:** volume, % first-pass match, exception ageing, touches per
invoice, cost per invoice (benchmark: `ap_cost_per_invoice`).

---

## 2. Order-to-Cash — hand-off map

```mermaid
flowchart LR
  subgraph Sales
    A1[Capture order] --> A2[Pricing / discount approval]
  end
  subgraph Credit
    A1 --> B1{Credit check} -- hold --> B2[Credit review] --> B1
  end
  subgraph Delivery
    B1 -- release --> C1[Fulfil / deliver] --> C2[Proof of delivery]
  end
  subgraph Billing
    C2 --> D1[Generate invoice] --> D2[Deliver invoice to customer]
  end
  subgraph Collections
    D2 --> E1[Dunning ladder] --> E2{Paid?}
    E2 -- no --> E3[Escalate / dispute] --> E4[Resolve dispute] --> E1
  end
  subgraph Cash application
    E2 -- yes --> F1[Receive remittance] --> F2{Auto-match}
    F2 -- no --> F3[Manual application] --> F4[Unapplied cash]
    F2 -- yes --> F5[Clear AR]
  end
```

**Where to look:** pricing exceptions creating billing disputes (policy) · credit limits reviewed
annually (policy) · invoice delivery by post/PDF email (technology) · collectors also handling
disputes and cash application (people) · unapplied cash with no ageing (process).

For depth here switch to the `ar-diagnostic` skill (06) — it carries the DSO/CEI/ADD baseline script.

---

## 3. Record-to-Report — close flow

```mermaid
flowchart TD
  A[Sub-ledger cut-off] --> B[Accruals and provisions]
  A --> C[Intercompany matching]
  B --> D[Journal posting]
  C --> D
  D --> E[Account reconciliations]
  E --> F{Review and approve}
  F -- issues --> D
  F -- clean --> G[Trial balance close]
  G --> H[Consolidation]
  H --> I[Management reporting]
  H --> J[Statutory / external reporting]
```

**Where to look:** intercompany differences found after cut-off (process) · manual and upload
journals as a share of postings (`je_automation`) · reconciliations in spreadsheets reviewed by
email (technology + policy) · rework loop F→D as the real driver of close length.

**Metric:** days from trial balance to consolidated statements (`close_days_monthly`).

---

## 4. Blueprint layers — target-state diagram

```mermaid
flowchart TD
  L1["<b>1. Value proposition</b><br/>role of finance - effort mix stewardship / operations / partnering"]
  L2["<b>2. Service delivery model</b><br/>retained - CoE - SSC - GBS - outsourced - automated - agentic"]
  L3["<b>3. Process architecture</b><br/>L1-L3 taxonomy, hand-offs, standards"]
  L4["<b>4. Data and technology</b><br/>application map, data domains, systems of record"]
  L5["<b>5. Organisation and talent</b><br/>roles, skills, spans, layers"]
  L6["<b>6. Governance and policy</b><br/>decision rights, policies, controls"]
  L7["<b>7. Performance management</b><br/>KPI tree, cadence, benefit tracking"]
  L1 --> L2 --> L3 --> L4
  L3 --> L5
  L2 --> L6
  L4 --> L7
  L5 --> L7
  L6 --> L7
```

Use with the consistency tests in `references/target-operating-model.md` §1 — the arrows are the
tests: a change in an upper layer that produces no change below it is the defect to hunt.

---

## 5. Current → target shift table

The most persuasive single page in an assessment deck. One row per headline shift, each tagged
with its lens and the initiative that delivers it.

| # | Dimension | Today | Target | Lens | Initiative |
|---|---|---|---|---|---|
| 1 | Invoice processing | 38% manual intervention, no-PO tolerated | Touchless standard path, no-PO-no-pay enforced | Policy | INI-02, INI-08 |
| 2 | Close | 9 days, 4 on intercompany | 5 days, intercompany matched pre-close | Process | INI-04 |
| 3 | Reporting | 3 versions of revenue by region | One definition, one owning system | Data | INI-05 |
| 4 | FP&A effort | 70% data preparation | 60% analysis | People | INI-05, INI-06 |
| 5 | Collections | Reactive, spreadsheet worklists | Behaviour-based dunning, automated matching | Process | INI-03 |
| 6 | Delivery model | Fragmented across 11 entities | GBS with E2E process ownership | People | INI-10 |

---

## 6. Roadmap wave diagram

```mermaid
gantt
  title Finance transformation roadmap
  dateFormat X
  axisFormat %s
  section Wave 1 - Prove
  Master data ownership and cleanse   :0, 4
  Intercompany calendar and ownership :0, 4
  Collections and cash application    :0, 6
  No-PO-no-pay enforcement            :4, 5
  section Wave 2 - Core
  Journal automation and reconciliation :6, 8
  Single reporting layer                :6, 12
  Touchless invoice processing          :9, 10
  Retire duplicate reports              :18, 3
  Driver-based rolling forecast         :18, 9
  section Wave 3 - Structural
  Finance delivery model move to GBS    :19, 18
```

Numbers are months from programme start and match `assets/initiative-backlog-template.csv` as
scheduled by `ft_analyze.py roadmap`. Regenerate after any change to the backlog rather than
editing this by hand.
