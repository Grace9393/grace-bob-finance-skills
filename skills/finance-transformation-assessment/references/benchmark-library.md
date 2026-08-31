# Benchmark Library — finance function, cross-industry and by sector

Canonical machine-readable values live in **`assets/benchmarks.csv`** — that file is what
`scripts/ft_analyze.py gap` reads. This document carries the citation discipline, the
interpretation rules, the industry guidance and the refresh procedure. **If you change a number,
change it in the CSV and re-render the snapshot in §2.**

---

## 0. Citation discipline — read before quoting anything

Every row carries a `confidence` flag. It governs what you may do with the number:

| Flag | Meaning | Permitted use |
|---|---|---|
| `verified` | Traced to a named published source with a date and a population | Quote on a client page **with the source and as-of date visible on that page** |
| `directional` | Practitioner range, no published source | Frame a range in discussion only. **Never** print as a benchmark figure, never put in a business case, never attribute to a third party |

Four ways benchmark comparisons go wrong — check each before you present:

1. **Denominator mismatch.** "Finance cost as % of revenue" depends entirely on what the client
   counts as finance. Reconcile scope first: does it include payroll? internal audit? finance IT?
   embedded business analysts? A client that excludes 200 embedded analysts will score in the top
   quartile without deserving it. State the scope you used on the page.
2. **Peer set mismatch.** Business model beats sector. A subscription software company and a
   project-based engineering firm share a sector code and share no finance economics. Where the
   published cut is unhelpful, use cross-industry and *say so* rather than borrowing a flattering
   sector row.
3. **Quartile theatre.** Top quartile is a distribution position, not a target. The relevant
   question is what the gap is worth (§3) and what it would cost to close — not the rank.
4. **Stale and blended data.** Different measures in a single table can be years apart. Every row
   here carries `as_of`; keep it visible when several rows appear on one page.

Chasing a single metric predictably distorts another. Name the pairing when you present:
close speed ↔ error/restatement rate · finance cost ↔ business partnering capacity ·
DSO ↔ revenue and customer relationship · AP cost per invoice ↔ early-payment discount capture.

---

## 1. Sources currently in the library

| Source | What it covers | Access |
|---|---|---|
| **APQC Open Standards Benchmarking** — finance organisation, AP, close | Cost, FTE, cycle time by quartile with sample sizes; industry cuts | Public summaries via APQC resource library and CFO.com "Metric of the Month"; full quartiles need APQC membership / Benchmarks on Demand |
| **The Hackett Group — Digital World Class Finance (June 2025)** | Relative performance deltas between Digital World Class and peer group | Public press release |
| **AR research pack** (`06-ar-diagnostic/references/ar-research-pack.md`) | DSO, CEI, ADD, aging, Atradius regional payment data | Local |

Notable gap: **no verified public quartile data for FP&A cycle metrics, forecast accuracy or
reconciliation automation.** Those rows are `directional`. If the engagement depends on them,
buy the benchmark or measure a peer set — do not fill the gap with a plausible number.

---

## 2. Snapshot of verified values

Rendered from `assets/benchmarks.csv`; the CSV is authoritative.

### Function-level (cross-industry)

| Metric | Top quartile | Median | Bottom quartile | Source / as-of |
|---|---|---|---|---|
| Total finance cost, % of revenue | 0.66% | 1.00% | 1.50% | APQC, Jan 2025 |
| ↳ top performers, revenue > $1B | 0.40% | — | — | APQC, 2025 |
| ↳ top performers, revenue < $1B | 0.90% | — | — | APQC, 2025 |
| Finance FTEs per $1B revenue | ≤36 | 69.4 | ≥141.6 | APQC, 2025 (n=1,784) |
| Monthly close, trial balance → consolidated statements | ≤5 days (some cuts 4.5) | 6.4 days | ≥10 days | APQC, 2025 |

Scale effect matters more than most clients expect: at >$1B revenue the top-quartile cost ratio
is less than half the <$1B figure. Never compare a mid-market client to a large-cap ratio.

### Process-level

| Metric | Top quartile | Median | Bottom quartile | Source / as-of |
|---|---|---|---|---|
| AP cost per invoice processed | ≤$2.07 | $5.83 | ≥$10.00 | APQC, 2024–25 (n=1,485) |
| DSO | ≤28–30 days | — | — | AR research pack |
| Collections effectiveness index | ≥80% | — | — | AR research pack |
| AR over 90 days past due | <3% | — | >5% | AR research pack |
| Journal entries posted without manual intervention | 99% (Digital World Class) | 85% (peer) | — | Hackett, Jun 2025 |
| AP workflows fully automated | ~80% (Digital World Class) | — | — | Hackett, Jun 2025 |

### AP cost per invoice — industry medians

| Industry | Median | Read |
|---|---|---|
| Distribution / transportation | $1.14 | High volume, high standardisation, strong e-invoicing |
| Consumer products | $4.58 | Near cross-industry median |
| Cross-industry | $5.83 | — |
| Public sector / government | $9.43 | Control-heavy, fragmented systems, low PO discipline |

The 8× spread between the best and worst industry medians is mostly **structural** (volume,
standardisation, e-invoicing maturity) rather than managerial. Use the industry median as the
fair comparison and cross-industry top quartile only to show the theoretical ceiling.

### Hackett Digital World Class deltas (relative, not absolute)

45% lower finance cost as % of revenue · up to 42% fewer FTEs across key functions ·
35–57% shorter close cycles · 57% less spent on planning and forecasting · 74% faster executive
insights · 57% faster forecasts · 48% lower DSO · 83% lower average days delinquent ·
68% more time on forward-looking analysis.

**These are ratios between two cohorts, not client targets.** The correct use is "organisations
in the top cohort operate at roughly half the cost" — never "you should be 45% lower."

---

## 3. From gap to value at stake

`ft_analyze.py gap` computes both. Two conversions only:

- **Cost-ratio metrics** (finance cost % of revenue, FTEs per $1B): value = (client − target) ×
  the client's own scale driver (revenue in $B, or FTE × fully-loaded cost).
- **Unit-cost metrics** (AP cost per invoice): value = (client unit cost − target) × annual volume.
- **Working-capital metrics** (DSO, DPO, inventory days): value = day-gap × average daily
  revenue (or COGS). This is a **one-time cash release**, plus a small recurring carry saving at
  the client's cost of capital — never a recurring P&L benefit. See
  `roadmap-and-business-case.md` §2.

Three rules:
1. Size the gap to the **median first**, then show top quartile as the stretch. Opening on top
   quartile invites the "we are not them" objection and loses the room.
2. Apply a realisation factor and show it. 100% gap closure has never happened.
3. **Value at stake ≠ benefit case.** Value at stake is the theoretical size of the prize;
   the business case is what the initiatives actually deliver, net of cost to achieve. Keep
   the two on separate pages, and never let the first migrate into the second.

---

## 4. Industry notes

Where a published industry cut is not available, use cross-industry and label it. These notes
shape *interpretation*, not the numbers:

- **Financial services / banking** — regulatory reporting dominates R2R; finance/risk data
  overlap; "finance cost" boundary with regulatory reporting must be defined explicitly.
- **Manufacturing** — cost accounting and inventory valuation carry the complexity; plant
  controllers usually sit outside the finance cost definition and must be reconciled in.
- **Retail / wholesale** — very high transaction volume, deductions and vendor allowances; cash
  application and dispute handling drive the O2C cost base.
- **Distribution / transportation** — the AP cost leader; high automation, standardised invoices.
- **Public sector** — highest AP unit cost; appropriation-based control, fragmented systems,
  procurement rules limit standardisation. Benchmark against public sector only.
- **Healthcare providers** — revenue cycle dominates and is not comparable to commercial O2C;
  use healthcare-specific revenue-cycle benchmarks or none.
- **Energy / utilities** — joint ventures, regulatory accounting and capital-project accounting
  add processes absent from the cross-industry definition.
- **Professional services** — project accounting, WIP and revenue recognition dominate; low
  transaction volume makes unit-cost benchmarks weak; prefer cycle-time and accuracy measures.

---

## 5. Refresh procedure

Re-verify before every new engagement, and at least every six months:

1. Check APQC's public metric pages and the CFO.com "Metric of the Month" series for updated
   quartiles — these carry the sample sizes needed for a defensible citation.
2. Check The Hackett Group newsroom for the current year's Digital World Class finance release.
3. Update `assets/benchmarks.csv`: value, `source`, `as_of`, `population`. Never edit a value
   without updating its date.
4. Promote a `directional` row to `verified` **only** with a named source, a date and a
   population. If you cannot name all three, it stays directional.
5. Re-render the §2 snapshot and note the change in the engagement's assumption log.

---

## Sources
- [APQC — Process frameworks and Open Standards Benchmarking](https://www.apqc.org/process-frameworks)
- [APQC — Finance Organization Key Benchmarks: Cross Industry](https://www.apqc.org/resource-library/resource-listing/finance-organization-key-benchmarks-cross-industry)
- [APQC — Finance FTEs per $1 Billion in Revenue](https://www.apqc.org/resource-library/resource/finance-ftes-1-billion-revenue)
- [APQC — Total Cost to Process Accounts Payable per Invoice Processed](https://www.apqc.org/resource-library/resource/total-cost-process-accounts-payable-invoice-processed)
- [APQC — Cycle Time to Perform the Monthly Close](https://www.apqc.org/resource-library/resource/cycle-time-perform-monthly-close)
- [CFO.com — Metric of the Month: Finance Function Cost](https://www.cfo.com/news/metric-of-the-month-finance-function-cost/659493/)
- [CFO.com — Metric of the Month: Finance FTEs Per $1B in Revenue](https://www.cfo.com/news/metric-of-the-month-finance-ftes-per-1b-in-revenue/658277/)
- [CFO.com — Metric of the Month: Accounts Payable Cost](https://www.cfo.com/news/metric-of-the-month-accounts-payable-cost/659393/)
- [The Hackett Group — Digital World Class Finance Teams Operate at 45% Lower Cost (Jun 2025)](https://www.thehackettgroup.com/the-hackett-group-digital-world-class-finance-teams-operate-at-45-lower-cost-and-deliver-faster-smarter-insights/)
- Local: `06-ar-diagnostic/references/ar-research-pack.md` (AR/O2C benchmarks and regional data)
