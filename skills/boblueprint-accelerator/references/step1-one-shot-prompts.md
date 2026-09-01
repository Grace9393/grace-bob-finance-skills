# Step 1 one-shot — research + schema in a single Bob run, no back-and-forth

Two ways to run it. Check which one applies: ask Bob *"Do you have web access / web search tools enabled in this workspace?"* — if yes, use **Prompt A** (Bob does the research itself). If not, run `harvest.py` once (see below), then use **Prompt B** on the harvested folder.

Both prompts carry the same **no-back-and-forth contract**: Bob must finish in one run, never ask a clarifying question, and record every assumption instead.

**Attach `ft-base-ontology.jsonld` to either prompt.** It is the practice's base ontology in the Entity / Operation / State pattern Context Studio imports (validated clean with `validate_ontology.py`). Bob extends it per client instead of inventing a schema shape from scratch — that's what prevents the "imports but the graph is empty" failure mode.

---

## Prompt A — Bob researches AND drafts the schema (web-enabled Bob)

```text
You are helping an IBM finance-transformation consultant prepare a client engagement. Work END-TO-END IN ONE RUN. Do not pause to ask me anything at any point: where information is missing or ambiguous, make the industry-standard assumption and record it in the ASSUMPTIONS section at the end.

CLIENT CONTEXT:
- Client: {{legal name + industry, e.g. "Acme Consumer Goods — CPG manufacturer, ~$8B revenue"}}
- Stock ticker (if listed): {{ticker or "privately held"}}
- Official website: {{https://...}}
- Process area in scope: {{e.g. "cross-process finance exception management (OTC, PTP, RTR, FP&A)"}}
- Engagement goal: {{e.g. "agentic target-state blueprint for exception orchestration"}}

PHASE 1 — RESEARCH (do all of this yourself, no questions):
1. Search the client's official website and investor-relations pages: strategy framework (name it — e.g. "EverGreen"), operating segments / regional structure, finance-organization structure, and any mentions of ERP/finance systems or transformation programs.
2. Capture the latest ORGANIZATION CHART from official sources: executive committee, managing/supervisory board, and finance leadership — names, exact job titles, and the page URL for each. Prefer the client's own leadership/governance pages; corroborate with the latest annual report's governance section.
3. Pull the latest ANNUAL FINANCIAL STATEMENTS — the 10-K/20-F from SEC EDGAR for US-listed clients, or the annual report PDF from the IR site otherwise (record title, publication date, period covered, and the direct PDF URL). Focus on: MD&A, segment reporting, and risk factors that touch finance processes (controls, close, receivables, restructuring).
4. Search for analyst coverage relevant to the process area — Gartner Magic Quadrant / Market Guide, IDC, Forrester — using only vendor-hosted licensed reprints on the vendor's own site. Do NOT attempt to access paywalled gartner.com content.
5. Search APQC-aligned public material for process benchmarks in the process area.
6. Build a CORPUS MANIFEST: for every source used — title, exact URL, access date, one line on what it contributed. Only sources in the manifest may be cited as evidence in the schema.

PHASE 2 — SCHEMA (from the Phase 1 corpus only):
The attached `ft-base-ontology.jsonld` is our practice's base ontology in the Entity / Operation / State pattern that IBM Context Studio imports. Produce the client-tailored ontology by EXTENDING it — keep its `@context` and every existing member unchanged (do not rename or remove anything). Tailor it by:
1. Adding client- and process-area-specific Entities (e.g. `ft:RebateClaim`, `ft:ExceptionCase`) as nouns discovered in the corpus, each with `attributes` (types: `string | integer | float | boolean | ENUM_A|ENUM_B | string|null`), `identityKey`, `humanRef`, and `invariant`.
2. Adjusting enum values inside `attributes` to the client's landscape (e.g. the client's actual ERP names in System usage notes, severity scales, cycle frequencies).
3. Adding Operations (verbs) between entities — every Operation needs `from`, `to`, `precondition`, `postcondition`; a good ontology has 1.5–3× more Operations than Entities.
4. Adding States only where a new entity has a real lifecycle; reference them from `hasState`, `initialState`, `terminalStates`.
5. Modeling the CORPORATE MASTER LAYER alongside the finance layer, per our [CLIENT] master-schema reference: `Executive` (from the org chart — jobTitle, LinkedIn where public), `Report` (from the financial statements — reportName, datePublished, temporalCoverage, pdfUrl), `Strategy` / `StrategicAction` (the named strategy framework), and `RegionalSubsidiary` (segments) — as Entities, connected with Operations like `CorporationHasExecutive`, `CorporationHasReport`, so the org chart and financial statements land as first-class graph members.
6. Recording evidence in `description` fields by citing the CORPUS MANIFEST entry (title + URL) — the ontology stays class-level; instance data arrives later when Context Studio ingests the documents.

HARD RULES (Context Studio import fails silently otherwise):
- Exactly two top-level keys: `@context` and `@graph`.
- Every `@graph` member has `id`, `type`, `name`; `type` is exactly one of `Entity`, `Operation`, `State`.
- Every Operation has `from` and `to`.
- Every cross-reference (`from`, `to`, `relatesTo`, `hasState`, `initialState`, `terminalStates`, `emitsEvent`) resolves to a member that exists in `@graph`.
- All ids use the `ft:` prefix; reference-valued `@context` entries keep their `"@type": "@id"`.

OUTPUT, in this exact order, in one response:
1. CORPUS MANIFEST (table)
2. The complete extended JSON-LD ontology (single fenced code block — base members plus your additions)
3. ASSUMPTIONS — every assumption you made instead of asking me
4. REVIEW NOTES — the 5 modeling decisions you are least certain about, so my review starts there

Do not produce any blueprint content — ontology only. This response is final; do not offer follow-up options or ask if I want changes.
```

---

## Prompt B — Bob drafts from a pre-harvested corpus (no web access)

One-time setup, once per client (~2 minutes):

```bash
cd boblueprint
cp client.example.json acme.json     # fill in: client, ticker, official pages, reprint URLs, your email
python harvest.py acme.json          # pulls EDGAR filing + official pages + reprints -> inputs/research/acme/
# drop any IBM-licensed Gartner/IDC PDFs into inputs/research/acme/ by hand — the manifest picks them up
```

Then attach (or point Bob's workspace at) `inputs/research/{{client}}/` and run:

```text
You are helping an IBM finance-transformation consultant prepare a client engagement. Work END-TO-END IN ONE RUN. Do not pause to ask me anything: where information is missing or ambiguous, make the industry-standard assumption and record it in the ASSUMPTIONS section at the end.

CLIENT CONTEXT:
- Client: {{industry, revenue, ERP}}
- Process area in scope: {{...}}
- Engagement goal: {{...}}

THE CORPUS: the attached folder is the complete research corpus, harvested today. `manifest.json` lists every document with its source and URL — treat it as the citation registry. Read every document before drafting. Do not cite anything outside the manifest.

TASK: the attached `ft-base-ontology.jsonld` is our practice's base ontology in the Entity / Operation / State pattern that IBM Context Studio imports. Produce the client-tailored ontology by EXTENDING it — keep its `@context` and every existing member unchanged (do not rename or remove anything). Tailor it by:
1. Adding client- and process-area-specific Entities (nouns discovered in the corpus, e.g. `ft:RebateClaim`, `ft:ExceptionCase`), each with `attributes` (types: `string | integer | float | boolean | ENUM_A|ENUM_B | string|null`), `identityKey`, `humanRef`, and `invariant`.
2. Adjusting enum values inside `attributes` to the client's landscape.
3. Adding Operations (verbs) between entities — every Operation needs `from`, `to`, `precondition`, `postcondition`; aim for 1.5–3× more Operations than Entities.
4. Adding States only where a new entity has a real lifecycle; reference them from `hasState`, `initialState`, `terminalStates`.
5. Modeling the CORPORATE MASTER LAYER alongside the finance layer, per our [CLIENT] master-schema reference: `Executive` (from any org-chart / leadership documents in the corpus), `Report` (annual financial statements — reportName, datePublished, temporalCoverage, pdfUrl), `Strategy` / `StrategicAction`, and `RegionalSubsidiary` — as Entities with Operations like `CorporationHasExecutive`, `CorporationHasReport`.
6. Recording evidence in `description` fields by citing the manifest entry (file + source + URL) — the ontology stays class-level; instances arrive when Context Studio ingests these documents.

HARD RULES (Context Studio import fails silently otherwise):
- Exactly two top-level keys: `@context` and `@graph`.
- Every `@graph` member has `id`, `type`, `name`; `type` is exactly one of `Entity`, `Operation`, `State`.
- Every Operation has `from` and `to`.
- Every cross-reference (`from`, `to`, `relatesTo`, `hasState`, `initialState`, `terminalStates`, `emitsEvent`) resolves to a member that exists in `@graph`.
- All ids use the `ft:` prefix; reference-valued `@context` entries keep their `"@type": "@id"`.

OUTPUT, in this exact order, in one response:
1. CORPUS COVERAGE — one line per manifest document: used / not relevant (and why)
2. The complete extended JSON-LD ontology (single fenced code block — base members plus your additions)
3. ASSUMPTIONS — every assumption made instead of asking me
4. REVIEW NOTES — the 5 least-certain modeling decisions

Ontology only — no blueprint content. This response is final; do not ask if I want changes.
```

---

## Why this removes the back-and-forth

| Old friction | What handles it now |
|---|---|
| "Can you send me the annual report?" | `harvest.py` pulls the latest 10-K/20-F from EDGAR automatically (or Prompt A has Bob fetch it) |
| "Which pages of the client site matter?" | `client.json` lists them once; the script fetches and cleans them |
| "Where did this claim come from?" | `manifest.json` is the citation registry; the schema's `ft:evidence` must reference it |
| Bob asks clarifying questions mid-run | The contract: one run, no questions, ASSUMPTIONS section instead |
| Multiple review round-trips | REVIEW NOTES pre-targets the 5 weakest decisions, so checkpoint 1 is a single focused pass |

**Gartner and other licensed research:** the script deliberately only fetches vendor-hosted *reprints* (publicly licensed). Full MQs/Market Guides come from IBM's analyst seat — download once, drop the PDF in the folder, and the manifest registers it as "hand-dropped (licensed analyst research)". Never scrape gartner.com.

**Financial data beyond the annual report** (quarterly trends, peer comparisons): add the IR quarterly-results URLs to `extra_urls` in the config. Keep it to public sources — this corpus travels into ICA in Step 2.

---

## After Bob returns — validate before Context Studio (part of Checkpoint 1)

Save Bob's ontology block as `schemas/{{client}}-v1.jsonld`, then:

```bash
python validate_ontology.py schemas/{{client}}-v1.jsonld
```

The validator catches exactly what makes Context Studio imports fail silently: dangling cross-references, duplicate or unprefixed ids, members missing `id`/`type`/`name`, Operations without `from`/`to`, and `@context` namespace mistakes. If it prints problems, paste the numbered list back to Bob with one line — *"Fix these validator findings; change nothing else."* — that's a mechanical fix-up, not a design conversation, so the one-shot contract holds. Import into Context Studio only on a clean exit.
