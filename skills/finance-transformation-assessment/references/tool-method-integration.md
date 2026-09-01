# Tool ↔ method integration

Four formerly separate skills now run as one. The assessment is the method. Context Studio,
Process Studio and the Blueprint Accelerator are the tools that serve it. This file records what
happens where they overlap, because three of the overlaps produce the same artifact twice.

Read it before running any generation step.

---

## 1. Artifact precedence

The tools generate fast. The method decides what is true. Where both produce the same thing, the
column on the right wins.

| Artifact | Produced by the tool | Produced by the method | Precedence |
|---|---|---|---|
| Target operating model | Process Studio, as an interactive HTML artifact | Phase 1, seven layers at Level 2 | **method** — the tool's TOM is an input to Phase 1, not a replacement |
| Business case | Process Studio, with NPV / IRR / payback / Monte Carlo | Phase 4, benefit taxonomy and ramps | **split** — tool models, method rules the benefits |
| Pain points | Procedure Eater, at corpus scale | Phase 3, five lenses with root cause | **method** — tool output enters as candidates |
| Process diagram | Process Studio BPMN / Mermaid | `swimlane-diagram` skill | either, stated on the page |
| Use-case blueprint | ICA generation in accelerator Step 3 | the contract in `house-style-and-blueprint-contract.md` | **contract** — counts are exact and enforced |
| Ontology / schema | Process Studio JSON-LD export | accelerator `ft-base-ontology.jsonld` | **accelerator base**, extended — see §6 |

The general rule holds even where this table has no row: **a generated artifact is a draft until its
numbers carry a client source or a cited benchmark.**

---

## 2. The two duplicated artifacts, in detail

### Target operating model

Both produce a TOM. They are not the same object and they use different role vocabularies.

| | Phase 1 TOM | Process Studio TOM |
|---|---|---|
| Shape | seven layers: value proposition, service delivery model, process architecture, data & technology, organization & talent, governance & policy, performance management | generated from the analysed corpus |
| Roles | client's own org, mapped to the delivery model options | human: Chief Accountability Officer · System Architect · Relationship Expert · Validator. AI: Reasoning Agent · Action Agent |
| Evidence | client interviews, capability assessment, maturity scoring | inference from the SOPs fed in |

**Do not run both and present both.** Generate the Process Studio TOM when a large SOP corpus
exists, read it as a fast first cut, then fold it into the Phase 1 TOM. Where the generated role
taxonomy is used on a client page, define the six roles on that page — the client has never seen
them, and "Chief Accountability Officer" is not a job title in their organisation.

### Business case

Process Studio's model is the better calculator. This skill's rules govern what may be counted.

Ten inputs it needs before it runs: volume · average handling time · FTEs involved ·
exception/rework rate · time per affected request · system upload volumes · approval delay ·
loaded labour rate · control incidents in the last 12 months · annual revenue scope.

Ask the client for each. The tool researches gaps when they are missing, and **a researched number
and a client number are not the same evidence.** Mark which is which on the page.

Then apply `roadmap-and-business-case.md` §2 to the output:

- never sum hard, soft, cost-avoidance and working-capital benefits into one headline
- FTE displacement is a hard saving only if the headcount actually leaves
- every benefit line carries a named accountable executive and a baseline metric, or it is an
  opportunity rather than a benefit

**The business case is a separate artifact from the blueprint.** ROI, NPV and payback live in the
business case. A TOM citing "Blueprint §6.2 ROI" cites a section that does not carry it.

---

## 3. Machine-surfaced findings are candidates, not findings

The Procedure Eater reads a whole corpus and surfaces triggers, actors, compliance considerations
and candidate use cases. That is discovery at a scale interviews cannot reach, and it is the basis
for finding **shared capability clusters** — one consolidated platform play instead of many one-off
automations.

What it returns is not yet a pain point. A pain point in this method carries:

| Required | Supplied by the tool? |
|---|---|
| Observation with evidence | usually yes |
| Primary lens (people / policy / process / data / technology) | no |
| Root cause, not symptom | rarely — it reports what the SOP says |
| Pain dimension | no |
| Severity × frequency × effort score | no |
| Golden thread step | sometimes |
| Named persona from the inventory | no |

So the flow is: Procedure Eater surfaces candidates → the interview and classification chain in
`pain-point-taxonomy.md` turns them into findings → the register carries them forward. Skipping the
middle step produces a register that is 90% "technology" lens, which is the signature of a
diagnosis that stopped at the first answer.

**The Process Analysis Report is the diagnosis, not the blueprint.** Review it before generating
anything downstream; a wrong diagnosis propagates into every artifact after it.

---

## 4. Data residency — check before the first upload

| Deployment | Client-confidential data? |
|---|---|
| Shared IBM instance (global) | **not allowed** — synthetic or public only |
| Regional IBM instance | allowed **with explicit client approval** and all security requirements met |
| Enterprise Advantage deployment (client's own cloud) | allowed |

A team boundary is an access boundary, not a residency class. "It is our team's instance" does not
answer this question.

This binds Phase 0 and Phase 3, the two phases that upload client material. Ingesting confidential
material into the wrong instance is not undone by deleting it afterwards.

**Ingestion limits differ between the two studios. Do not conflate them.**

| | Process Studio | Context Studio |
|---|---|---|
| Per file | 10 MB | — |
| Per batch | 2,000 files staged | 30 files / 100 MB |
| Total | 500 MB | — |
| Parallelism | 1–32, default 4 | — |

---

## 5. Product claims are directional

The studio overview material quotes 3–5× faster delivery, 1,400+ SOPs analysed in under three days,
and 200+ active users in two weeks of alpha.

These are product claims with no stated population and no baseline. Under `benchmark-library.md`
§0 they are **`directional`**: usable to frame an opportunity in conversation, never placed on a
client page as a benchmark. Never present the SOP-throughput figure as a delivery commitment.

---

## 6. Which ontology is authoritative

Two schemas exist and they serve different ends.

- **`assets/ft-base-ontology.jsonld`** — the accelerator base. Extend it with the client's corporate
  master layer: Executive (org chart), Report (financial statements), Strategy / StrategicAction,
  RegionalSubsidiary. Validate with `scripts/validate_ontology.py` and import only on CLEAN.
- **Process Studio JSON-LD export** — generated from the analysed corpus, and only produced when
  "Include JSON-LD Ontologies" is ticked at project creation. Nothing downstream can import a schema
  that was never generated.

**Rule:** the accelerator base is authoritative for the client master layer. The generated export
extends the process layer. Where the two disagree on an entity, the validated base wins and the
difference goes into the schema — then re-import. Never patch the graph directly; the fix does not
survive the next ingest.

---

## 7. Four persona vocabularies, not one

`golden-threads.md` §4 documents three unreconciled persona sets: the RTR thread, the OTC thread,
and the accelerator inventory. The Process Studio TOM adds a fourth vocabulary — six generated
roles that describe accountability, not people.

| Vocabulary | Use it for |
|---|---|
| Accelerator inventory | **the source of truth for drafted blueprints** |
| RTR / OTC thread personas | modal conversion, mapped to an inventory archetype |
| Process Studio TOM roles | describing the target operating model's accountability split |

Map thread personas to an inventory archetype and raise a `persona_flag` for anyone with no match.
Never silently carry a thread persona into a blueprint. Never treat a generated TOM role as a
person.

---

## 8. The chain, end to end

```
Phase 0   research → ft-base-ontology extended → validate CLEAN
          → Context Studio: ingest, curate, verify, expose over MCP   [Valid + MCP]
             │
Phase 1   ← generated TOM (fast first cut, optional)
          golden thread scope → seven-layer TOM → capability sheet          [Gate 1]
             │
Phase 2   client metrics → benchmark gap → value at stake
             │
Phase 3   Procedure Eater over the SOP corpus → candidates
          → five-lens classification → pain point register + maturity        [Gate 2]
             │
Phase 4   initiative backlog → wave plan → business case
          → blueprint queue by golden thread step                            [Gate 3]
             │
Phase 5   EAEF blueprint / use-case blueprints → Excel model → deck          [Gate 4]
          → implementation spec → coding agent
```

Each arrow is a hand-off where evidence can be lost. The gates exist at the four points where it
most often is.

---

## 9. What each absorbed skill contributed

Recorded so the merge can be audited, and so nothing is assumed lost.

| Former skill | What moved into this one |
|---|---|
| `ica-process-studio` (10) | the four-stage loop, Procedure Eater, EAEF library and blueprint sections, autonomy zones, the ten artifact types, export discipline, data residency, the business case inputs |
| `ica-context-studio` | schema design, source connectors, Docling extraction, graph curation, MCP exposure, the "no authoring API" constraint, the choose-between-alternatives table |
| `boblueprint-accelerator` (03) | the four-step production line, one-shot research prompts, the base ontology and its validator, the harvest script, the build kit, `[SENIOR REVIEW]` discipline, the timed-metric rule |

The originals remain installed and are unchanged. Retire them only after this skill has run a full
engagement, and retire by moving them aside rather than deleting in place.
