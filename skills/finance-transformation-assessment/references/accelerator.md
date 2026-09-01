# The Blueprint Accelerator — four-step production line

Absorbed from the former `boblueprint-accelerator` skill (03). It turns one-shot client research
into a validated ontology, then into use-case blueprints and a branded deck.

Human checkpoints sit at every handoff. Never skip a gate.

Where this runs inside the assessment: **Step 1 and Step 2 are Phase 0**, Step 3 is the drafting
named at the end of Phase 4, and Step 4 is part of Phase 5.

---

## 1. Research → schema

Inputs: client name, ticker or domain, process area. Two modes.

**Web-enabled.** Run Prompt A in `step1-one-shot-prompts.md`. Research the official site, capture
the latest organization chart with names, exact titles and URLs, and the annual financial
statements with title, date, period and PDF URL. Capture analyst reprints from vendor-hosted
sources only — never paywalled originals. Build the corpus manifest, then extend
`assets/ft-base-ontology.jsonld`.

One run. Record assumptions instead of asking questions.

**No web.** The human runs `python scripts/harvest.py <client>.json` first, configured from
`assets/client.example.json`. Draft from the harvested folder with Prompt B.

Model the corporate master layer: Executive (org chart), Report (financial statements),
Strategy / StrategicAction, RegionalSubsidiary — per the reference shape in the prompts file.

**Gate 1.** Output REVIEW NOTES listing the five least-certain decisions. The human runs:

```
python scripts/validate_ontology.py <schema>.jsonld
```

Fix findings if asked, changing nothing else. Import to Context Studio only on CLEAN.

Which schema is authoritative when Process Studio also emits one: `tool-method-integration.md` §6.

---

## 2. Context Studio import and verification

The human imports the schema and ingests the corpus. Help verify with three grounding questions:

1. personas and pain points
2. system access
3. evidence

Recurring fixes go into the schema, then re-import. **Never patch the graph** — the fix does not
survive the next ingest.

Mechanics are in `ica-studios.md` §2. Residency is in `tool-method-integration.md` §4 and must be
settled before anything uploads.

---

## 3. Generate and pressure-test

Preferred path: the AAS workflow — Blueprint Generator → Method Pressure-Tester → human gate.

Fallback, always available: run the two prompts in `build-kit.md` §3a and §3b manually in Process
Studio plus a chat assistant.

The blueprint contract is enforced and its counts are exact: narrative → **4** pain points → **3**
agents → user benefits → **4** business benefits → checkpoint flags. The full contract, the closed
enums and the archetypes are in `house-style-and-blueprint-contract.md`.

Inputs come from the assessment, not from invention. Per draftable initiative, carry forward the
`process_area`, the four pain points, the personas and the SOW excerpt and interview notes. Build
the queue with:

```
python scripts/ft_golden_thread.py queue <backlog.csv> --register <register.csv>
```

Where the golden thread step already carries a prototype modal, you are **converting, not
drafting** — the two structural deltas are in `golden-threads.md` §3.

**Never pad to hit a count.** Where the register cannot supply a fourth evidenced pain point or a
third benefit for a role, raise a checkpoint flag naming what is missing.

**Never propose an agent without a named human approver and a pause trigger.**

**Gate 3.** Every FLAG resolved or justified before sign-off.

---

## 4. Blueprint → deck

Render with the prompt in `build-kit.md` §Step 4: house structure and tone, IBM-branded template.

**Insert `[SENIOR REVIEW]` markers where the blueprint lacks content. Never invent.** Summarize
every marker you inserted.

The accelerator's own 10-slide pitch deck has a slot-by-slot spec at
`H:\My Drive\AA\blueprint-accelerator\slide-spec.md`. Use it rather than rebuilding.

Deck rendering goes through the `ibm-branded-pptx` skill. Chart styling follows `dataviz`.

**Gate 4.** Run the completeness check in `deliverable-standards.md` §5 and lint the house style
with `scripts/ft_house_style.py`. Nothing SOX-relevant reaches a client without senior consultant
sign-off.

---

## 5. The working surface and the metric

Team workbench — search console, schema generator, in-browser validator, run timers:
`https://claude.ai/code/artifact/1b4139c7-cc70-4cfb-882a-f12bedc6c0f1`

Start the timer at Step 1 and stop at Gate 4 sign-off. Log the real minutes in `runlog.md`. The
baseline it compares against is a day-plus of hand assembly.

**Never quote a cycle time that was not timed.**

---

## 6. Working material

- `step1-one-shot-prompts.md` — Prompt A (web-enabled) and Prompt B (harvested), with the
  reference ontology shape.
- `build-kit.md` — the Step 3a / 3b generation and pressure-test prompts, and the Step 4 render
  prompt.
- `proposal.md` — the accelerator's own proposal text.
- `video-script.md` — the demo narration.
- `assets/ft-base-ontology.jsonld` — the schema base to extend.
- `assets/client.example.json` — harvest configuration.
- `scripts/harvest.py`, `scripts/validate_ontology.py`.
