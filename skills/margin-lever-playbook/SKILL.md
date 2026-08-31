---
name: margin-lever-playbook
description: Map identified margin, cost, or cash risks to specific, prioritized corrective actions with expected-impact ranges and owners. Use this skill whenever the user asks "what should we do", "what actions should we take", "how do we fix/protect margin", "recommend levers", or requests recommendations after a variance analysis, forecast, or performance review has surfaced risks — e.g. "biggest risks to margin this quarter and what actions should we take". Always run this AFTER the diagnostic (financial-variance-analysis or a forecast) so recommendations tie to quantified drivers, never to generic advice.
---

# Margin Lever Playbook

Turn a quantified diagnosis into a decision-ready action plan. This skill assists with analysis workflows and is not financial advice; recommendations require review and approval by accountable finance leadership before execution.

## Prerequisite

Recommendations must anchor to named, quantified drivers from a prior diagnostic (a variance bridge, forecast gap, or trend analysis). If no diagnosis exists in context, run `financial-variance-analysis` first — never dispense levers against an unquantified problem.

## Workflow

1. **Restate the exposure.** One line per risk: driver, $ impact, direction, confidence (e.g. "Consulting gross margin −110bps vs plan, ~$18M, driven by utilization at 71% vs 76% target").
2. **Select candidate levers** from the library below — only those whose trigger condition matches a diagnosed driver. 3–6 levers maximum; a list of twelve is a menu, not a recommendation.
3. **Size each lever** with an expected-impact range and time-to-impact, derived from the diagnosed numbers (e.g. "+2pts utilization ≈ +$7–9M gross profit over two quarters"). Ranges, never point estimates.
4. **Score and rank** on impact × feasibility × speed. State trade-offs and second-order risks honestly (e.g. price increases risk churn; headcount actions carry severance cost and delivery risk).
5. **Assign the decision.** Each lever gets a proposed owner (CFO / CPO / segment lead), a decision needed, and a review checkpoint. Actions execute only after human approval — flag any follow-on workflow as requiring sign-off before triggering.

## Lever library

**Gross margin / delivery**
- Utilization recovery (bench redeployment, demand-supply rebalancing) — trigger: utilization below target
- Pricing and rate-card actions; discount governance — trigger: rate/price erosion in the bridge
- Delivery mix shift toward automation/reuse of assets — trigger: cost-to-serve rising faster than revenue
- Subcontractor-to-employee rebalancing — trigger: elevated contractor cost ratio
- Contract remediation on loss-making engagements — trigger: negative-margin accounts identified

**Operating expense**
- Discretionary spend controls (travel, events, external services) — trigger: discretionary OpEx above plan; fast but small
- Vendor consolidation and renegotiation — trigger: contractual-cost creep
- Span-of-control and organizational simplification — trigger: SG&A ratio deterioration; slow but structural
- Automation of manual finance/ops workflows — trigger: headcount-driven cost growth in support functions

**Working capital / cash**
- DSO reduction (billing cadence, collections escalation, disputed-invoice triage) — trigger: DSO above peer or trend
- DPO optimization within supplier terms — trigger: paying ahead of terms
- Unbilled/WIP burn-down — trigger: contract-asset growth outpacing revenue
- Inventory or prepayment tightening — trigger: current-asset build in the balance-sheet bridge

**Revenue quality**
- Backlog conversion acceleration on signed work — trigger: book-to-bill above 1 with soft in-quarter revenue
- Mix shift toward higher-margin offerings in pipeline gating — trigger: mix effect negative in rate/mix decomposition
- Churn/renewal defense on at-risk recurring revenue — trigger: ARR or renewal deterioration

## Output format

Lead with a one-paragraph recommendation summary (which 2–3 levers, expected combined impact range, key trade-off). Then a table: Lever | Addresses driver | Expected impact | Time to impact | Trade-off / risk | Owner | Decision needed. Close with what NOT to do — one or two superficially attractive actions that the diagnosis argues against, with the reason.

## Quality bar

Every recommendation must name the driver it addresses, quantify from diagnosed numbers, state its trade-off, and identify its decision owner. Reject generic output ("optimize costs", "improve efficiency") — if a lever could be pasted into any company's plan unchanged, it has not met the bar.

## Hand-offs

- Diagnosis missing → `financial-variance-analysis` (or `annual-report-analyzer` for public-company inputs)
- Action plan as tracker → `xlsx` skill
- Leadership readout → `ibm-branded-pptx` / `file-to-pptx`
- Approved follow-on workflows → orchestration layer (e.g. watsonx Orchestrate) with human-in-the-loop sign-off
