# Pain Point Taxonomy — the five-lens diagnostic

The purpose of this phase is not to collect complaints. It is to convert what people report into
**classified, evidenced, root-caused findings** that a roadmap can be built on. A pain point that
cannot be traced to a lens and a root cause is not yet a finding.

Lens vocabulary is shared with the maturity model in `target-operating-model.md` §4, so scores and
findings reconcile against each other.

---

## 1. The five lenses

| Lens | Covers | Typical evidence | The trap |
|---|---|---|---|
| **People** | Roles, capacity, skills, spans, key-person dependency, incentives, culture | Org data, FTE effort split, vacancy/turnover, cross-training coverage | "We need more people" is almost never the root cause — it is the symptom of process, data or policy failure upstream |
| **Policy** | Policies, controls, thresholds, approval rules, decision rights, statutory constraint | Policy documents with dates, approval matrices, exception logs | Policy that exists but is unenforced is a *different* finding from policy that is absent. Say which |
| **Process** | Design, standardisation, hand-offs, rework loops, cycle times, exception volume | Process maps, hand-off counts, rework/exception counts, cycle-time samples | Documented process ≠ actual process. Walk a live transaction |
| **Data** | Definitions, master data, quality at source, ownership, lineage, reporting consistency | Duplicate/incomplete master data counts, reconciliation differences, competing report versions | Data problems surface where they hurt, which is rarely where they are caused. Trace to point of entry |
| **Technology** | System landscape, integration, fit, automation, access, technical debt | Application inventory, interface map, manual workaround inventory, version/support status | Every lens gets blamed on technology by default. Require evidence that the system *cannot* do it, not that it *is not* doing it |

**Assign one primary lens per pain point** (secondary lenses optional). The distribution across
lenses is itself a finding: a register that is 80–90% technology means the interviews stopped at
the first answer, and the roadmap built on it will buy tools and change nothing.

Healthy registers usually land roughly 15–25% people, 10–20% policy, 25–35% process, 15–25% data,
15–25% technology. Treat that as a smell test for interview quality, not a target.

---

## 2. Interview guide

Six to twelve interviews per E2E process; always include one **doer** per hand-off, not only
managers. Managers describe the designed process; doers describe the real one.

**Opening (5 min)** — purpose, confidentiality (findings are aggregated and never attributed),
no system or person is on trial.

**Core questions:**
1. Walk me through what you actually do in a normal week for this process — step by step.
2. Where does the work come to you from, and where does it go next? What arrives wrong, and how
   often? *(hand-off quality — the richest single question)*
3. What do you do outside the system? Which spreadsheets, mailboxes or trackers do you keep, and
   what would break if you stopped? *(shadow process inventory)*
4. What did you rework or chase last month, and why?
5. When something is wrong or unclear, who decides? How long does that take?
6. What have you already tried to fix? What stopped it? *(surfaces prior failure and the real
   constraint — often policy or ownership, rarely technology)*
7. If one thing changed tomorrow, what would you pick, and what would it be worth?
8. What do you know that people upstream of you don't? *(finds root causes located elsewhere)*

**Close** — quantification: how many, how often, how long, what does it cost when it goes wrong.
Ask for the artefact (the tracker, the report, the email chain). **An interview that produces no
number and no artefact produces no finding.**

**Discipline:** never accept the first cause. Ask "why does that happen?" until the answer is
something the client can actually change (usually three to five iterations). Stop when the answer
crosses into another lens — that is the root cause, and it goes on the register under *that* lens.

---

## 3. Observation → root cause → lens

Record every pain point as a chain. Example rows:

| Observation (evidenced) | Immediate cause | Root cause | Primary lens |
|---|---|---|---|
| 38% of invoices need manual intervention | No PO on invoice | Requisition policy not enforced; buying outside the channel has no consequence | Policy |
| Close takes 9 days, 4 spent on intercompany | Intercompany differences found late | No agreed intercompany settlement calendar or single owner | Process |
| Three versions of "revenue by region" circulate | Each function builds its own extract | No agreed definition and no owning system of record | Data |
| Analysts spend 70% of the month on data prep | Data pulled and cleansed by hand | Reporting layer requires manual assembly across two ERPs | Technology |
| Cash application backlog of 11 days | Remittances arrive in a shared mailbox | Role never redesigned after the bank changed reporting format | People |

Traps this format prevents: recording the symptom as the finding, blaming the visible system, and
producing recommendations that treat causes located in a different lens.

---

## 4. Scoring and prioritisation

Score each pain point on three dimensions, 1–5:

- **Severity** — consequence when it occurs. 1 nuisance · 3 material rework or delay ·
  5 financial misstatement, compliance breach, customer/regulatory impact.
- **Frequency** — 1 rare (annual) · 3 monthly · 5 continuous/daily.
- **Effort to fix** — 1 trivial (days, no system change) · 3 moderate (weeks, config/policy) ·
  5 major (months, platform or organisational change).

`impact = severity × frequency` (1–25). Prioritisation quadrants:

| | Low effort (1–2) | High effort (4–5) |
|---|---|---|
| **High impact (≥12)** | **Do now** — Wave 1 | **Plan properly** — Wave 2/3, business case required |
| **Low impact (<12)** | **Batch** — bundle into housekeeping | **Park** — record and revisit; do not spend roadmap capacity |

Rules that keep the register honest:
- Every pain point gets a **quantified basis** — count, cycle time, error rate or cost. "Frequent"
  and "significant" are not scores.
- Every pain point names the **process owner** who confirmed it.
- Compliance and control findings **bypass the quadrants**: a control gap is remediated regardless
  of effort, and is flagged separately for the audit/control owner.
- Pain points that repeat across entities are **consolidated** and their frequency raised — not
  listed five times, which quietly inflates the register and hides the real top ten.

---

## 5. Cross-cutting patterns

When several pain points share a root cause, promote the pattern to a **theme** — themes, not
individual pain points, are what the deck presents and what initiatives map to. Recurring ones:

- **Shadow finance.** Work has migrated to spreadsheets and mailboxes around a system that no
  longer fits. Symptom: the volume of trackers found in question 3. Root cause is usually a
  process or fit gap, never "user preference."
- **Exception as the norm.** The standard path handles a minority of volume. The design question
  is which exceptions to eliminate, not how to process them faster.
- **Ownership vacuum at hand-offs.** Every step has an owner; the transitions have none. Shows up
  as reciprocal blame between adjacent teams.
- **Control by inspection.** Quality assured by downstream checking rather than prevention at
  source — expensive, late, and it hides the defect rate.
- **Data debt paid downstream.** Bad master data created once, corrected repeatedly by everyone
  who touches it, and never fixed at the source.
- **Standardisation blocked by a real constraint.** Sometimes the local variant is legally or
  contractually required. Verify — and where it is real, record it as a design constraint rather
  than a pain point, or the roadmap will promise something that cannot be delivered.

---

## 6. Register columns

Use `assets/pain-point-register-template.csv`. Columns: `id`, `process` (L2 from the taxonomy),
`observation`, `evidence`, `quantum`, `immediate_cause`, `root_cause`, `lens`, `secondary_lens`,
`severity`, `frequency`, `effort`, `owner_confirmed`, `theme`, `initiative_id`.

Every register row must end up either linked to an initiative in the backlog or explicitly parked
with a reason. Unlinked findings are how a client concludes the assessment produced a list rather
than a plan.
