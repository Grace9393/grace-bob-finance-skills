# AR Diagnostic Assessment — Research & Resource Pack

Collected 2026-07-24. Mapped to the two SOW deliverables: **Diagnostic Findings Report** (Week 4) and **AR Improvement Roadmap**.

---

## Part 1 — Diagnostic Findings Report: what to collect per section

### 1.1 AR performance baseline and KPI observations

Core KPI set to baseline (each with benchmark anchors):

| KPI | Formula / definition | Benchmark |
|---|---|---|
| DSO (Days Sales Outstanding) | (AR / credit sales) × days | Top performers ≤28–30 days; median ~36–46 days (Hackett / APQC) |
| Best Possible DSO (BPDSO) | (Current AR / credit sales) × days | Gap vs DSO isolates overdue drag |
| ADD (Average Days Delinquent) | DSO − BPDSO | Separates terms problems from collection-execution problems |
| CEI (Collection Effectiveness Index) | Collected vs collectible in period | ≥80% healthy; ≥85% strong; <50% urgent |
| % AR >90 days past due | Aging bucket share | <3% product firms, <5% service firms |
| % invoices overdue | Share of B2B invoices paid late | 44–53% regionally (Atradius 2025) — see 1.7 |
| Bad debt % of B2B invoices | Write-offs vs credit sales | 6–8% regionally (Atradius 2025) |
| Auto cash-application rate | % payments applied without touch | Key automation-maturity indicator |
| Unapplied cash balance & age | Payments not matched to invoices | Leading indicator of data/remittance issues |
| Dispute/deduction volume, cycle time, recovery rate | Per exception category | 55% of AR pros cite disputes as toughest task |

Context stat: Hackett's 2025 Working Capital Survey estimates **~$600B of excess working capital locked in US receivables** if median firms hit top-quartile DSO/collections — a strong executive-summary hook.

Sources: [Balance AR efficiency benchmarks](https://www.getbalance.com/post/ar-efficiency-benchmarks/) · [Esker AR KPI benchmarking](https://www.esker.com/blog/invoice-cash/mastering-ar-kpis-benchmarking-metrics-matter-most-accounts-receivable/) · [Billtrust 2026 AR Benchmark Report](https://www.billtrust.com/resources/blog/2026-accounts-receivable-benchmark-report) · [Serrala AR KPIs & benchmarks](https://www.serrala.com/blog/accounts-receivable-kpis-and-benchmarks-measure-and-improve-ar-performance) · [IntelliChief DSO guide](https://www.intellichief.com/dso-kpi/) · [ApprovalMax AR KPIs](https://blog.approvalmax.com/accounts-receivable-kpis)

### 1.2 Hand-offs (process baseline)

Use the **APQC Process Classification Framework (PCF)** order-to-cash decomposition as the neutral reference map for hand-off analysis: manage sales orders → process customer credit → deliver → invoice → process AR → manage collections → manage adjustments/deductions → apply cash. Hand-off friction typically concentrates at: sales→credit (terms exceptions), delivery→billing (billing triggers), billing→collections (invoice quality), payment→cash application (remittance data).

Sources: [APQC end-to-end O2C mapping](https://www.apqc.org/resource-library/resource-listing/end-end-mapping-order-cash-process) · [APQC: what is order-to-cash](https://www.apqc.org/blog/what-order-cash-process) · [APQC O2C process maps & measures](https://www.apqc.org/resource-library/resource-listing/end-end-process-maps-and-measures-order-cash) · [APQC O2C performance assessment](https://www.apqc.org/what-we-do/benchmarking/assessment-survey/order-cash-performance-assessment) · [APQC PCF v7.4 PDF](https://solutions.ifrc.org/sites/default/files/2024-10/K014750_APQC%20Process%20Classification%20Framework%20(PCF)%20-%20Cross%20Industry%20-%20PDF%20Version%207.4.pdf)

### 1.3 Key pain points and recurring exception categories

Working taxonomy (four exception classes, each mappable to root cause):

1. **Data exceptions** — inaccurate customer master, wrong PO/billing data, missing remittance detail
2. **System exceptions** — multiple ERPs, manual re-keying between systems, email/spreadsheet workflows
3. **Policy exceptions** — regional or customer-specific terms, non-standard discounts/approvals
4. **Customer exceptions** — short pays, deductions (promotions/returns/shortfalls), combined payments, disputes (pricing, misapplied payments, inability to pay)

Unapplied cash is the cross-cutting symptom of all four; each deduction typically requires individual review/validation/resolution (heavy in CPG & manufacturing).

Sources: [Emagia: unapplied cash](https://www.emagia.com/resources/glossary/unapplied-cash-in-cash-application/) · [Stuut: short pays & deductions](https://www.stuut.ai/blog/cash-application-exception-handling-short-pays-and-deductions) · [Billtrust dispute management guide](https://www.billtrust.com/resources/ebooks/effective-dispute-management-in-accounts-receivable-guide) · [HighRadius AR process & optimization](https://www.highradius.com/resources/Blog/the-accounts-receivable-process-cycle-steps-optimization-with-templates/) · [Predicting exceptions in AR (LinkedIn)](https://www.linkedin.com/pulse/predicting-exceptions-accounts-receivables-sayantan-datta)

### 1.4 Findings from selected AR examples

Method references for sampling and walking transactions end-to-end (aging deep-dive, trend and ratio analysis, invoice-level tracing):
[Gaviti: how to conduct AR analysis](https://gaviti.com/how-to-conduct-an-accounts-receivable-analysis/) · [Invoiced: performing AR analysis](https://www.invoiced.com/resources/blog/how-perform-accounts-receivable-analysis) · [AccountingTools: AR auditing](https://www.accountingtools.com/articles/accounts-receivable-auditing)

### 1.5 Policy, data, ownership and technology contributors

Assess against: credit policy currency and enforcement, terms governance, master-data quality, ERP/tooling fragmentation, RACI clarity across credit/billing/collections/cash-app. (APQC PCF "Establish AR policies" is the anchor sub-process.)

### 1.6 Reporting and visibility gaps

Check for: real-time aging visibility, forecast-to-collection linkage, exception dashboards, DSO/CEI trending, and whether aging is segmented by *reason* (willingness-to-pay / dispute class) rather than only days-past-due.

### 1.7 Market differences (external benchmarks by region)

Atradius Payment Practices Barometer 2025:

| Region | Overdue B2B invoices | Notes |
|---|---|---|
| Central & Eastern Europe | ~53% (highest) | Bad debts ~8% of B2B invoices |
| Western Europe | ~47% | Bad debts ~6%; delays driven by financial stress |
| North America | ~44% | Terms ~43 days; US DSO ~47 days |
| Asia | ~44% | Stable/improving DSO trend |

Sources: [Atradius North America 2025](https://group.atradius.com/knowledge-and-research/reports/b2b-payment-practices-trends-in-north-america-2025) · [Atradius Asia 2025](https://atradius.us/knowledge-and-research/reports/b2b-payment-practices-trends-asia-2025) · [Atradius Western Europe 2025](https://group.atradius.com/knowledge-and-research/reports/b2b-payment-practices-trends-western-europe-2025) · [Atradius CEE](https://atradius.us/knowledge-and-research/reports/b2b-payment-practices-trends-central-and-eastern-europe-2026) · [Atradius US 2025 PDF](https://group.atradius.com/dam/jcr:5609b617-ac29-4e30-8b01-0663a01d94bd/payment-practices-barometer-us-2025-en.pdf)

### 1.8 Executive observations and recommendations

Frame around: cash unlock opportunity (DSO gap × daily credit sales), effort unlock (exception volumes × handling time), and risk (bad-debt exposure vs regional norms).

---

## Part 2 — AR Improvement Roadmap: frameworks & content sources

- **Stop / Change / Add** — classify every recommendation: *Stop* (redundant reports, manual chasing where auto-dunning fits), *Change* (policy thresholds, hand-off ownership, aging segmentation), *Add* (auto cash application, exception dashboards, AI collections prioritization).
- **Prioritization** — 2×2 of cash/effort impact vs implementation complexity; sequence into near-term (0–3 mo, policy & quick wins), mid-term (3–9 mo, workflow/automation), long-term (9+ mo, platform/AI agents).
- **Automation opportunity landscape (2026)** — behavior-based collections replacing email blasts; aging categorized by willingness-to-pay; agentic AR (reasoning over payment history, balance size, prior outreach to choose next action); auto cash application; dispute triage.
  Sources: [HighRadius: AI in AR use cases](https://www.highradius.com/resources/Blog/ai-in-accounts-receivable/) · [Kapittx: AR software vs AI agents](https://kapittx.com/accounts-receivable-software-vs-ai-agents-for-accounts-receivable/) · [Kapittx: automating AR with AI agents](https://kapittx.com/automate-accounts-receivable-with-ai-agents-in-2026/) · [Paraglide: AI agents automate AR](https://www.paraglide.ai/blog/how-ai-agents-automate-accounts-receivable) · [Nuvo: AI agents for AR](https://nuvo.com/resources/ai-agents-for-accounts-receivable-uses-tools-and-how-they-work) · [Beam AR agent template](https://beam.ai/agents/accounts-receivable-agent/)

---

## Part 3 — Reusable skills / capabilities already available

### In this Claude environment (finance plugin, loaded)
`finance:reconciliation`, `finance:variance-analysis`, `finance:financial-statements`, `finance:close-management`, `finance:journal-entry(-prep)`, `finance:audit-support`, `finance:sox-testing` — plus `daloopa:working-capital` (DSO/DPO/DIO analysis) and `data:*` skills for building the KPI baseline and dashboards.

### Local package (H:\My Drive\AA\Claude_Plugins_Skills_Package)
Only `daloopa/working-capital` and `daloopa/supply-chain` mention receivables — there is **no dedicated AR-operations skill** in the exported 42-plugin package. Gap worth filling.

### External / GitHub (candidates to adapt)
1. **[loopfour/finance-skills](https://github.com/loopfour/finance-skills)** (MIT, JustPaid) — closest match; SKILL.md format, drop-in for Claude Code or Bob:
   - `skills/ar-collections` — AR aging review, overdue prioritization, collector worklists
   - `skills/dunning-emails` — customer-safe reminder sequences
   - `skills/payment-reconciliation` — payment/remittance/invoice/bank matching
   - `skills/invoice-health-check` — invoice completeness + collection-risk scoring
   - Design principle: evidence-based, human approval before irreversible actions
2. **Commerce Accounts Receivable** community skill ([mcpmarket listing](https://mcpmarket.com/tools/skills/commerce-accounts-receivable), [claudskills mirror](https://claudskills.com/skills/commerce-accounts-receivable/)) — AR aging across 30/60/90+ buckets, dunning logs, credit memos, bad-debt write-offs; installs under `~/.claude/skills/`
3. **Skill directories to mine further**: [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) (330+ skills incl. finance/commercial), [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills), [GetBindu/awesome-claude-code-and-skills](https://github.com/GetBindu/awesome-claude-code-and-skills)

### Suggested build
An `ar-diagnostic` skill combining: KPI baseline calculator (Section 1.1 formulas + benchmarks) → exception taxonomy classifier (1.3) → findings-report generator matching the SOW deliverable structure → Stop/Change/Add roadmap generator. Reuse loopfour's `ar-collections` as the operational core; the deliverable templates come straight from this pack.
