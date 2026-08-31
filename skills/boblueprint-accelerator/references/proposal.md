# Proposal 3 — Boblueprint: Customized Blueprints for Context & Process Studio (Grace)

**2026 IBMer watsonx Challenge — business proposal + technique. Status: BUILT — this doc indexes the working assets.**

---

## Business proposal

**Executive summary.** Every finance-transformation engagement hand-builds two foundations: a client domain schema with grounded context, and use-case blueprints across process areas. It takes a day-plus of scarce senior time per use case and comes out structurally different every time. Boblueprint is a repeatable Bob + ICA pipeline that turns public research (official org chart, financial statements, analyst reprints) into a validated Context Studio schema and a pressure-tested, branded blueprint deck — first draft in under an hour, consultant approving at every gate.

**Value.** Cycle time ~1 day+ → <1 hour per use case (~45 min for the blueprint draft); consistent house structure; each client schema becomes a compounding, reusable practice asset (asset-based consulting). Answers the "1,000 schemas in six months" scaling worry with one shared base ontology + validator-gated per-client extensions.

**Commercial angle.** Directly accelerates every ICA-based engagement (Nestlé, Heineken pattern); the productivity story GMs already track (ICA adoption charts). No client prerequisite beyond what engagements already have.

**2026 fit.** The definitional case: everyday repeatable usage, only Bob + the three ICA studios, human-in-the-loop structural (approval gate inside the agent workflow).

---

## Technique

### What Bob does
1. **Step 1 — research → schema:** one-shot run (no clarifying questions; assumptions recorded): captures official org chart → `Executive` entities, financial statements → `Report` entities, strategy → `Strategy`/`StrategicAction`, then **extends** the practice base ontology in the Entity/Operation/State import format.
2. **Step 4 — blueprint → deck:** renders the signed-off blueprint into the branded PPTX; gaps become `[SENIOR REVIEW]` markers, never invented content.
3. Built all the tooling below during development — and rebuilds/extends it on camera during the challenge window.

### What ICA does
1. **Context Studio:** imports the validated schema, ingests the research corpus, populates the knowledge graph (verified with three grounding questions).
2. **Agentic App Studio workflow:** `Blueprint Generator` agent (Process Studio project on the Context) → `Method Pressure-Tester` agent (PASS/FLAG vs IBM method) → **human approval gate** → release. Two agents built during the challenge; A2A/Orchestrate integration is the stretch.
3. **Process Studio:** cognitive decomposition, agent register, target operating model generation.

### Built assets (all working today)

| Asset | Location |
|---|---|
| Interactive workbench (research console, search links, JSON-LD schema generator + download, in-browser validator, live prompts, run-log timers) | https://claude.ai/code/artifact/1b4139c7-cc70-4cfb-882a-f12bedc6c0f1 |
| Research harvest (EDGAR 10-K/20-F, official pages, analyst reprints → manifest'd corpus) | `boblueprint/harvest.py` + `client.example.json` |
| Base ontology (10 Entities, 19 Operations, 10 States; `EscalatesTo` human-gate invariant) | `boblueprint/ft-base-ontology.jsonld` |
| Import-shape validator | `boblueprint/validate_ontology.py` |
| One-shot Bob prompts (A: web-enabled; B: harvested corpus) | `boblueprint/step1-one-shot-prompts.md` |
| Full pipeline runbook incl. ICA API automation | `watsonx-challenge-2026-build-kit.md` |
| Reference outputs | `heineken-master-schema_test.jsonld`, `coca-cola-master-schema.jsonld` (ClientZero Studio) |
| Submission one-pager, deck, demo script | `watsonx-challenge-2026-merged-submission.*`, `-deck.pptx`, `-demo-script.md` |

### Demo & metric
Two runs through one unchanged workflow (repeatability proof): Run 1 = Joe's exception-orchestration scenario; Run 2 = Kate's CFO co-pilot scenario. Timer on screen: day-plus baseline → <1 hour. Run-log rows generate from the workbench.

### Risks & mitigations
- **AAS availability day one:** documented fallback — same prompts run manually in Process Studio + a chat assistant.
- **Schema sprawl:** base-ontology discipline + validator gate (already enforced).
- **"Just prompting?" objection:** the pipeline is agents + gates + validators + reusable assets — shown live.
