# Transformation Roadmap and Business Case

The roadmap converts findings into a sequenced, owned, funded plan. The business case makes it
survivable at the investment committee. Both fail the same way: benefits that nobody owns and a
sequence that ignores dependency.

---

## 1. Roadmap construction

### 1.1 From findings to initiatives

Every initiative traces to the pain points it resolves (`initiative_id` on the register). Initiatives
that resolve nothing on the register are either missing a finding or are somebody's pet project —
resolve which before it reaches the roadmap.

Each initiative carries: `id`, `name`, `description`, `pain_point_ids`, `lens`, `type`
(Stop / Change / Add), `benefit_category`, `benefit_annual`, `cost_onetime`, `cost_run_annual`,
`effort` (1–5), `impact` (1–5), `duration_months`, `depends_on`, `owner`, `wave`.

**Stop / Change / Add** is the classification clients act on:
- **Stop** — work that should cease entirely (reports nobody reads, duplicate reconciliations,
  manual controls superseded by automated ones). Cheapest benefit available and consistently
  under-used. Always hunt for these first; a roadmap with no Stop items has not looked hard.
- **Change** — existing work redesigned, standardised or automated.
- **Add** — new capability that does not exist today (a CoE, a planning platform, a data layer).

### 1.2 Sequencing

Three waves, sequenced by dependency and by the client's absorption capacity:

| Wave | Horizon | Contains | Purpose |
|---|---|---|---|
| **1 — Prove** | 0–6 months | Policy fixes, Stop items, config changes, quick automation, data cleanup at source | Fund credibility. Self-financing or near it |
| **2 — Core** | 6–18 months | Process standardisation, delivery-model moves, core automation, reporting layer | Where most benefit lands |
| **3 — Structural** | 18–36 months | Platform replacement, GBS/organisation change, advanced analytics and agentic capability | Only what genuinely requires the foundation from Waves 1–2 |

Sequencing rules, in priority order:
1. **Dependencies bind.** Standardise before you centralise; centralise before you outsource;
   fix data at source before you build reporting on it; make the process standard before you
   automate it. Violating any of these is the most common cause of Wave 2 overrun.
2. **Wave 1 must produce visible, measurable results within one reporting cycle.** Programmes that
   show nothing for nine months lose their sponsor.
3. **Respect absorption capacity.** Count the change load per team — the same twelve controllers
   cannot absorb four parallel initiatives. This constraint, not analytical ambition, sets pace.
4. **Do not stack two go-lives on a close or year-end.** Check the finance calendar before dates.
5. **Leave contingency in Wave 2**, where scope discovery always lands.

`ft_analyze.py roadmap` enforces dependencies (an initiative cannot start in an earlier wave than
its predecessors), produces the impact/effort matrix, and flags dependency violations rather than
silently resequencing.

---

## 2. Benefit taxonomy — never blend these

| Category | Definition | Presentation rule |
|---|---|---|
| **Hard / cash P&L** | Reduces actual spend: headcount, contractor, vendor, licence, external fees | Only these may be committed to a budget line. Name the budget and the accountable executive |
| **Cost avoidance** | Spend that will not now be incurred: avoided hires, avoided licences, avoided remediation | Real but not extractable from a budget. Present separately, always labelled |
| **Working capital** | Cash released by DSO/DPO/inventory improvement | **One-time cash release**, plus a recurring carry saving at the client's cost of capital. Presenting a one-time release as a recurring benefit is the fastest way to lose CFO trust |
| **Productivity / capacity** | Hours released | State whether hours convert to headcount (then it is hard) or to redeployed capacity (then it is not a saving). Say which, explicitly |
| **Risk and control** | Reduced misstatement, compliance, audit or penalty exposure | Qualitative or expressed as exposure reduction. Never monetised into the headline |
| **Revenue / service** | Faster decisions, better pricing, fewer customer-impacting errors | Attribution is weak; present as an upside case, outside the base business case |

Rules:
- **One headline number, one category.** If the deck says "$14M benefit," it must be the hard
  benefit. Everything else appears as a separate labelled line beneath.
- **Every benefit has a baseline metric, an owner and a measurement date.** Without all three it
  is an opportunity, not a benefit (Gate 3 in SKILL.md).
- **Show the realisation factor.** Typical planning discipline is 60–80% of the theoretical gap,
  ramped. State the factor you used and why.
- **Never double count.** A single FTE released cannot appear under both an AP automation
  initiative and a shared-services move. Deduplicate at the FTE and cost-line level, not the
  initiative level.

### Benefit ramp

Benefits do not start at go-live. Default ramp, adjusted per initiative type:

| Months after go-live | 0–3 | 4–6 | 7–12 | 13+ |
|---|---|---|---|---|
| % of steady-state benefit | 0% | 25% | 60% | 100% |

Policy and Stop initiatives ramp faster (often 50% immediately). Organisation and delivery-model
moves ramp slower and usually dip first — productivity falls during transition, and a case that
does not show the dip will be disbelieved by anyone who has run one.

---

## 3. Value driver tree

Connect financial outcome to operational lever so every initiative can be traced upward. Build it
top-down, and only include drivers you can actually measure:

```
Finance value
├── Cost of finance
│   ├── Labour cost ── FTE count ── volume × unit time × (1 − automation rate)
│   │                            └─ rework rate, exception rate, span of control
│   ├── Technology cost ── licences, infrastructure, application count
│   └── Third-party cost ── outsourcing, audit, advisory fees
├── Cash and working capital
│   ├── DSO ── billing accuracy, dispute rate, collections effectiveness, terms compliance
│   ├── DPO ── terms, payment run discipline, early-discount capture
│   └── Inventory days ── (where in scope)
├── Insight and decision quality
│   ├── Cycle time ── close days, forecast cycle, reporting latency
│   └── Accuracy ── forecast error, restatements, adjustment volume
└── Risk and control
    ├── Control effectiveness ── manual vs automated controls, exception volume
    └── Compliance ── audit findings, late filings, penalties
```

Use it two ways: to test that each initiative moves a named driver, and to show the CFO which
levers were *not* pulled and why.

---

## 4. Cost to achieve

Understating this is the second-most common business case defect (after unowned benefits).
Include all six: external services (advisory, SI, provider) · software and licences ·
internal effort (backfill and opportunity cost — cost it, do not call it free) · one-time
transition (recruitment, training, parallel running, severance) · run-rate change (new platform
run cost, retained-org cost) · contingency (15–25% by wave, higher for Wave 3).

---

## 5. Business case output

`ft_analyze.py roadmap` produces the cumulative net-benefit curve; the workbook renders it.
Present: total investment · annual benefit at steady state by category · net cash flow by year ·
payback period · NPV at the client's discount rate (ask; never assume) · benefit ramp by wave ·
sensitivity (at minimum: benefits at 70% realisation, costs at +20%, and both together).

Show the downside case yourself. A case with only an upside reads as a sales document, and the
CFO's own team will produce the downside anyway — better that it is yours and defensible.

---

## 6. Risk, change and governance

**Risks to name explicitly** (with owner, likelihood, impact, mitigation, and a trigger for the
mitigation): sponsorship change · absorption capacity · data quality worse than assessed on
inspection · ERP or platform roadmap collision · statutory/local constraints blocking
standardisation · key-person dependency during transition · benefit realisation lag ·
provider/contract dependency.

**Change impact** — for each initiative record who is affected, how their work changes, what they
must learn, and what they lose. Roadmaps that record only the technical change deliver systems
into unchanged behaviour, and the benefit never appears.

**Governance to stand up in Wave 1**, before initiatives start: a steering committee with decision
authority (not a review forum) · named E2E process owners · a benefit tracking mechanism against
baselines captured *now*, since a baseline cannot be reconstructed after the change · a change
control route for scope · a design authority to hold the blueprint's design principles when local
exceptions are requested — which they will be, from Wave 2 onward.
