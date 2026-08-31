---
name: ar-diagnostic
description: Conduct an Accounts Receivable diagnostic assessment — build the AR KPI baseline (DSO/BPDSO/ADD/CEI/aging), classify pain points and exception categories, compare against external benchmarks, and produce the two SOW deliverables (Diagnostic Findings Report and Stop/Change/Add AR Improvement Roadmap). Use when the user mentions AR assessment, receivables diagnostic, DSO/aging analysis, collections effectiveness, invoice-to-cash review, dunning, or the AR Improvement Roadmap.
---

# AR Diagnostic Assessment — conduct guide

You are conducting a consulting-grade AR assessment that ends in two deliverables:
**(1) Diagnostic Findings Report** and **(2) AR Improvement Roadmap**. Two hard rules:
1. **Every number in the findings report traces to client data or a cited benchmark** — never estimate a KPI; if data is missing, list it under "Areas requiring further analysis."
2. **You draft customer communications (dunning, statements); humans send them.**

## Step 1 — Build the KPI baseline

Get invoice-level data as CSV (columns: `invoice_id, customer, amount, issue_date, due_date, paid_date` — blank `paid_date` = open; optional `exception_category`). If none is available yet, demo with sample data:

```
python scripts/ar_kpi_baseline.py --make-sample
python scripts/ar_kpi_baseline.py sample_data/invoices.csv --asof 2026-06-30
```

Output is a markdown baseline: DSO, Best-Possible DSO, ADD, CEI, aging buckets, % >90 days, and exception counts. Compare each metric against the benchmark table in `references/ar-research-pack.md` §1.1 (DSO top quartile ≤28–30d, CEI ≥80%, <3–5% over 90 days) and flag every gap.

## Step 2 — Map hand-offs and classify pain points

Walk the invoice-to-cash flow against the APQC O2C decomposition (research pack §1.2): sales→credit→delivery→billing→collections→cash application→deductions. For each observed pain point, assign one of the four exception classes (§1.3): **data / system / policy / customer**. Unapplied cash and disputes get root-caused, not just counted. Use the operational vocabulary in `references/ar-operations-taxonomy.md` (aging-bucket actions, dunning ladder, credit-memo and write-off reasons) so findings use standard AR language.

## Step 3 — Draft the Diagnostic Findings Report

Follow the SOW section order exactly: baseline & KPI observations · hand-offs · pain points & exception categories · findings from selected AR examples · policy/data/ownership/technology contributors · reporting & visibility gaps · market differences (Atradius regional table, §1.7) · executive observations. Lead the executive section with the cash-unlock estimate: (DSO − top-quartile DSO) × daily credit sales.

## Step 4 — Build the AR Improvement Roadmap

Classify every recommendation **Stop / Change / Add**, score on cash-and-effort impact vs implementation complexity, and sequence: near-term (0–3 mo, policy & quick wins), mid-term (3–9 mo, workflow/automation — auto cash application, behavior-based dunning), long-term (9+ mo, platform/agentic AR). Every item gets an owner and dependencies. Close with immediate next steps and the further-analysis list from Step 1's data gaps.

## Gates
- Present the Step 1 baseline for confirmation before drafting findings — wrong source data invalidates everything downstream.
- Write-offs, credit memos, or any ledger action proposed in the roadmap are recommendations only; they require the client's approver and GL account per their policy.

## References
- `references/ar-research-pack.md` — KPI formulas & benchmarks, APQC hand-off map, exception taxonomy, Atradius regional data, automation landscape, all sources.
- `references/ar-operations-taxonomy.md` — operational AR vocabulary (buckets, dunning ladder, statuses, credit-memo/write-off reasons).
