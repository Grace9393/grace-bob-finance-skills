---
name: boblueprint-accelerator
description: Conduct the Finance Transformation Blueprint Accelerator — one-shot client research (official org chart, financial statements, analyst reprints) into a validated Context Studio ontology, then blueprint generation with ICA and branded deck rendering. Use when the user mentions Boblueprint, blueprint accelerator, client schema/ontology, Context Studio import, master schema, use-case blueprints, or watsonx Challenge proposal 03.
---

# Boblueprint — conduct guide

You (Bob) are conducting the 4-step accelerator. Human checkpoints at every handoff; you never skip a gate.

## Step 1 — Research → schema (you, one shot)

Inputs: client name, ticker/domain, process area. Two modes:
- **Web-enabled:** run Prompt A in `references/step1-one-shot-prompts.md` — research the official site, capture the LATEST organization chart (names, exact titles, URLs) and annual financial statements (title, date, period, PDF URL), analyst reprints (vendor-hosted only — never paywalled gartner.com), build the corpus manifest, then EXTEND `assets/ft-base-ontology.jsonld`. One run; record assumptions instead of asking questions.
- **No web:** the human runs `python scripts/harvest.py <client>.json` first (config: `assets/client.example.json`); you draft from the harvested folder with Prompt B.

Model the corporate master layer: Executive (org chart), Report (financial statements), Strategy/StrategicAction, RegionalSubsidiary — per the reference shape in the prompts file.

**Gate 1:** output your REVIEW NOTES (5 least-certain decisions); the human runs
`python scripts/validate_ontology.py <schema>.jsonld` — fix findings if asked ("change nothing else"), import to Context Studio only on CLEAN.

## Step 2 — Context Studio (human + you verifying)

Human imports the schema and ingests the corpus. Help verify with three grounding questions (personas/pain points; system access; evidence). Recurring fixes go into the schema, then re-import — never patch the graph.

## Step 3 — Generate + pressure-test (ICA agent workflow)

Preferred: the AAS workflow (Blueprint Generator → Method Pressure-Tester → human gate). Fallback (always available): run the two prompts in `references/build-kit.md` §3a/§3b manually in Process Studio + a chat assistant. **Gate 3:** every FLAG resolved or justified before sign-off.

## Step 4 — Blueprint → deck (you)

Render with the prompt in `references/build-kit.md` §Step 4: house structure and tone, IBM-branded template, and **insert [SENIOR REVIEW] markers where the blueprint lacks content — never invent**. Summarize every marker you inserted.

## Working surface
The team workbench (search console, schema generator, in-browser validator, run timers): https://claude.ai/code/artifact/1b4139c7-cc70-4cfb-882a-f12bedc6c0f1

## Metric to capture
Start the timer at Step 1, stop at Gate 4 sign-off; log the real minutes in `runlog.md` (baseline: a day-plus hand-assembly). Never quote a cycle time that wasn't timed.
