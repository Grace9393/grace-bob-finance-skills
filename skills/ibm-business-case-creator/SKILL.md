---
name: ibm-business-case-creator
description: Create comprehensive, persuasive business cases for client decision-making. Use when clients need to justify technology investments, process improvements, strategic initiatives, automation proposals, transformation programs, or executive funding requests. Selects the right business case framework for the situation, compares options including do nothing, quantifies costs and benefits, addresses stakeholder objections, and produces structured decision-ready business case documents or executive investment memos.
metadata:
  skills-suggested:
    - ibm-question-decomposer-direct
---

# IBM Business Case Creator

Create persuasive, evidence-based business cases that drive client action.

## When to Use

- Client needs to justify technology investment to stakeholders
- Proposal requires financial business case with ROI analysis
- Internal IBM opportunity requires business case to secure funding
- Client asks "how do I convince leadership to approve this?"
- Need to structure chaotic opportunity information into decision-ready format

## Framework Selection

Start by choosing the lightest framework that still fits the decision:

1. Use `references/five-case-model.md` by default.
   - Best for formal investment cases, public-sector style approvals, or multi-stakeholder decisions.
2. Use `references/roi-business-case.md` for narrow cost-savings, automation, productivity, or efficiency asks.
   - Best when the user mainly needs quantified pain, costs, benefits, payback, and a recommendation.
3. Use `references/change-business-case.md` when adoption, stakeholder alignment, and organisational change are central.
   - Best for transformation, operating-model change, or behaviour/process change.
4. Use `references/executive-investment-memo.md` when the user needs a short board/CFO/executive approval paper.
   - Best for 1-2 page decision memos.

If the context is ambiguous, high-stakes, or discovery-heavy, read `references/business-case-dimensions.md` and use it to identify missing information before drafting.

If the user wants a visual business case summary, timeline, ROI chart, break-even view, or decision-ready economics dashboard, generate the written case first and then use:

```bash
uv run python $SKILL_DIR/scripts/render_business_case_viz.py \
  --input <json-file> \
  --output <html-file> \
  --png-output <png-file>
```

Use `assets/business_case_viz_example.json` as the schema reference.
The visualization input must use explicit `scenarios.base_case`, `scenarios.best_case`, and `scenarios.worst_case` blocks so payback, ROI, and assumptions stay aligned.

## Core Principles

| Element | Key Questions |
|---------|---------------|
| Problem | What pain exists? What is the cost of inaction? Why now? |
| Options | What are the realistic options, including do nothing? |
| Financial | What investment is required? What benefits, payback, and sensitivities exist? |
| Evidence | What proof points, credibility, and risk reduction exist? |
| Stakeholders | Who decides? What do they care about? What objections must be addressed? |
| Delivery | What roadmap, governance, and success measures make this credible? |

## Workflow

### Phase 1: Discovery (15-20 min)

1. **Gather Context Documents**
   - Read any client materials (RFPs, presentations, emails)
   - Extract: problem description, stakeholders, constraints, existing data

2. **Choose the business case framework**
   - Select one reference document from the Framework Selection section
   - State the chosen framework briefly in the response if it affects structure or tone
   - Default to Five Case Model unless the ask is clearly narrower or shorter

3. **Identify Information Gaps**
   - Which dimensions are answered by existing materials?
   - Which require assumptions? (flag clearly)
   - Which require client input? (prepare questions)
   - If discovery is unusually complex, optionally use `ibm-question-decomposer-direct` to expand the problem space before writing

### Phase 2: Analysis (20-30 min)

4. **Build Financial Model**
   - **Costs**: Implementation (direct + indirect), ongoing operational
   - **Benefits**: Cost savings, revenue protection/uplift, productivity, risk mitigation
   - **Timeline**: Monthly cash flow, break-even point, 3-year NPV
   - **Scenarios**: Best case, base case, worst case

5. **Gather Evidence**
   - Proof points: IBM case studies, reference clients, analyst reports
   - Risk mitigation: phased approach, pilots, contractual protections, fallbacks
   - Credentials: IBM certifications, domain expertise, client testimonials

6. **Map Stakeholders** (use `ibm-story-stakeholder-mapping` if available)
   - Decision makers: sponsors, budget holders, technical authorities
   - For each: What do they care about? What concerns do they have?

7. **Compare Options**
   - Include a realistic do-nothing baseline
   - Include 2-3 viable approaches where possible
   - Explain why the preferred option wins on value, risk, timing, or strategic fit

### Phase 3: Synthesis (15-20 min)

8. **Structure the Business Case Document**

```
Executive Summary (1 page max)
- The ask in one sentence
- The problem and cost of inaction (3 bullets)
- The options considered and preferred recommendation
- The financial case (payback, annual benefit)
- Why low risk (3 bullets)
- Why now (2 bullets)

Strategic Case / Problem Statement
- Current state pain (quantified)
- Cost of inaction
- Desired future state
- Urgency drivers

Options Considered
- Do nothing / status quo
- Minimal intervention
- Preferred option
- Why preferred option is recommended

Financial Justification
- Investment required (table: direct, indirect, ongoing)
- Benefits (table: savings, revenue, productivity, risk)
- Payback and NPV
- Sensitivity analysis (best/base/worst)

Evidence, Credibility, and Commercial Confidence
- Proof points (case studies, references)
- Risk mitigation strategies
- Vendor credentials
- Delivery or contractual protections if relevant

Stakeholder Analysis
- Decision makers and their priorities
- Objections and responses
- Governance process and timeline

Implementation Roadmap and Benefits Realization
- Phased delivery plan
- Success metrics (leading and lagging)
- Baseline and target measures
- Risk mitigation
- Ongoing support plan

Appendices
- Detailed financial model
- Case studies
- Technical architecture (if relevant)
```

9. **Apply Persuasion Principles**
   - **Quantify everything**: "improves efficiency" → "returns 1.8 FTE, £50k/year"
   - **Conservative modeling**: use worst-case assumptions, highlight upside
   - **Evidence-based**: every claim backed by data, case study, or validation
   - **Risk-aware**: acknowledge risks explicitly, show mitigation plans
   - **Stakeholder-tailored**: address each decision-maker's priorities

### Phase 4: Quality Check (5 min)

- [ ] Problem quantified with metrics?
- [ ] Strategic alignment or business rationale made explicit?
- [ ] Options compared, including do nothing?
- [ ] Financial model includes costs, benefits, payback, scenarios?
- [ ] Evidence includes case studies and risk mitigation?
- [ ] Stakeholders identified with tailored value propositions?
- [ ] Implementation roadmap with success metrics and benefit tracking?
- [ ] Executive summary fits on one page?
- [ ] Conservative assumptions flagged ("at worst", "at least")?
- [ ] Quick wins or early value highlighted?
- [ ] Urgency clearly established?
- [ ] Funding strategy addresses budget constraints?

## Output Format

Default: **Markdown document** with executive summary + 5 sections + appendices.

Optional: **Slide deck** (use `frontend-slides` or `pptx` skill).

If the user asks for a short approval paper, use the executive memo framework and produce a 1-2 page memo rather than a full business case.

If the user asks for visual support, also produce a standalone HTML visualization covering current state, implementation period, future state, break-even point, ROI, and assumptions. Use explicit base/best/worst scenarios rather than mixing narrative qualifiers with one set of economics. If the visual is likely to be reused in slides or documents, also export a PNG.

## Integration with Other Skills

| Skill | Use for |
|-------|---------|
| `ibm-question-decomposer-direct` | Deep discovery when the problem is ambiguous or the user wants a decomposition tree |
| `ibm-story-stakeholder-mapping` | Detailed stakeholder analysis (section 4) |
| `ibm-story-objection-intelligence` | Anticipate and counter objections (section 4.2) |
| `ibm-bid-win-themes` | Compelling value propositions (executive summary) |

## References

- `references/five-case-model.md`: Default framework for formal business cases
- `references/roi-business-case.md`: Lean ROI-led framework for cost-savings and automation cases
- `references/change-business-case.md`: Framework for change-heavy transformation cases
- `references/executive-investment-memo.md`: Short executive decision memo format
- `references/business-case-dimensions.md`: Deep question bank for discovery and gap analysis
- `assets/business_case_viz_example.json`: Example input schema for business case visuals
- `scripts/render_business_case_viz.py`: Standalone HTML renderer for business case visuals

## Common Pitfalls to Avoid

- **Vague problem statements**: "Process is inefficient" → "Process takes 3.5 min vs 0.5 min industry best practice"
- **No options analysis**: If you do not compare against do nothing or a lighter alternative, the recommendation looks pre-decided
- **Optimistic financial modeling**: Use worst-case scenarios, flag assumptions
- **Missing stakeholder concerns**: Identify objections proactively, provide responses
- **No risk mitigation**: Acknowledge risks explicitly, show how they are managed
- **Implementation hand-waving**: "We'll implement it" → detailed roadmap with phases, metrics, risks
- **Executive summary too long**: Must fit on one page — decision-makers won't read more
- **No urgency**: Explain why acting now matters (deadlines, windows closing, costs accumulating)

## What Makes a Business Case Persuasive

### 1. Problem Articulation
Quantify the pain. "Manual PDF reading" becomes "3,150 hours/year (1.8 FTE) at £50.4k annual cost." Decision-makers need numbers to justify approval.

### 2. Cost of Inaction
Make delay expensive. Every month without the solution costs X. Competitors are moving. Regulatory deadlines are approaching.

### 3. Options Credibility
Show that alternatives were considered fairly. Decision-makers trust a recommendation more when they can see why the status quo and lighter options were rejected.

### 4. Conservative Financial Modeling
Use worst-case assumptions and say so. "At worst, 15-month payback. At least, £37.4k annual benefit." Credibility comes from honesty about uncertainty.

### 5. Low-Risk Framing
Explicitly state what the solution is NOT. "Not customer-facing. Not autonomous. Not replacing human judgment." Narrow scope reduces perceived risk.

### 6. Proof Points
"IBM has delivered this exact capability elsewhere." Named clients, specific numbers, transferable code. Evidence beats assertions.

### 7. Funding Strategy
Remove budget as a blocker. "Delivered within existing contract underspend — no additional charges." Make the financial path frictionless.

### 8. Stakeholder Alignment
Tailor the value proposition to each decision-maker. CFO needs IRR. CTO needs architecture confidence. Operations needs efficiency proof.

### 9. Governance Path
Show you understand their approval process. Name the committees, the timeline, the documentation required. Demonstrates competence.

## SPEN Agentforce Example

The SPEN proposal illustrates all key elements:

| Element | SPEN Example |
|---------|-------------|
| Problem quantification | 54k cases × 3.5 min = 3,150 hrs/year (1.8 FTE) |
| Cost of inaction | £50.4k/year accumulating |
| Financial case | 15-month break-even, £37.4k/year ongoing |
| Low-risk framing | Not customer-facing, not autonomous, not replacing judgment |
| Proof point | IBM delivered this capability elsewhere, code accelerator exists |
| Funding strategy | Uses £41k contract underspend — no new budget |
| Governance path | SDA/AI approvals acknowledged, effort included |
| Quick win | 4-week pilot with go/no-go gate before full rollout |
