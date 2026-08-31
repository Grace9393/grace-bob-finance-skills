# Build Kit — Finance Transformation Blueprint Accelerator ("Boblueprint")

**2026 IBMer watsonx Challenge — implementation guide: Bob prompts + ICA steps + optional API automation**

This is the working companion to the submission outline and demo script. It contains everything the team needs to actually run the four-step pipeline: copy-paste prompts for IBM Bob, click-path steps for the ICA studios, and optional Python automation against the ICA REST API.

> Build all of this **inside the challenge window (July 8–22)**. Keep this kit and the run logs in the team Box folder — Box is the recommended collaboration surface for the challenge.

---

## Folder layout (team Box folder)

```
boblueprint/
├── inputs/
│   ├── research/           # IBV PoVs, Gartner MQs, McKinsey, APQC extracts (per run)
│   ├── sow/                # sanitized SOW / engagement brief
│   └── interviews/         # current-state interview notes
├── schemas/                # Bob-drafted JSON-LD schemas, one per client/run
├── blueprints/             # Process Studio exports
├── decks/                  # rendered PPTX first drafts
├── prompts/                # this kit's prompts, versioned as we tune them
└── runlog.md               # timings + checkpoint decisions (judging evidence)
```

---

## Step 1 — Draft the schema (IBM Bob)

> **One-shot mode (preferred):** Step 1 can run without any back-and-forth. `boblueprint/harvest.py` (configure `client.json` once per client) pulls the research corpus automatically — latest 10-K/20-F from SEC EDGAR, official-site pages, vendor-hosted analyst reprints — into `inputs/research/<client>/` with a `manifest.json` citation registry. Then a single Bob run drafts the schema under a no-questions contract (assumptions get recorded, not asked). Prompts and setup: `boblueprint/step1-one-shot-prompts.md` — Prompt A if Bob has web access (Bob researches itself), Prompt B on the harvested corpus otherwise. The master prompt below is the interactive fallback.

### 1a. Master prompt — schema drafting

Paste into Bob with the research files attached or in the workspace. Replace the `{{...}}` slots.

```text
You are helping an IBM finance-transformation consultant prepare a client engagement.

TASK: Read the attached research corpus ({{list the files: IBV PoV, Gartner MQ, APQC PCF extract, interview notes}}) and draft a client-specific domain schema as JSON-LD, using schema.org as the base vocabulary with a custom `ft:` namespace for finance-transformation concepts.

CLIENT CONTEXT:
- Client: {{industry, e.g. "CPG manufacturer, ~$8B revenue, SAP S/4HANA"}}
- Process area in scope: {{e.g. "cross-process finance exception management (OTC, PTP, RTR, FP&A)"}}
- Engagement goal: {{e.g. "agentic target-state blueprint for exception orchestration"}}

THE SCHEMA MUST MODEL, at minimum:
1. Process areas and sub-processes in scope (align names to the APQC PCF where possible)
2. Roles/personas (as schema.org Person subtypes with `ft:responsibleFor` relations)
3. Systems of record (ERP, workflow, reporting, ticketing) and the data objects that flow between them
4. Pain points (as `ft:PainPoint`, each linked to a process, a persona, and a system)
5. Candidate agents (as `ft:Agent`, each with `ft:addressesPainPoint` and `ft:requiresAccessTo` relations)
6. Benefits (`ft:UserBenefit` linked to personas; `ft:BusinessBenefit` framed as risk-reduction, cycle-acceleration, governance, or scalability)

RULES:
- Reuse entity and persona names from our prior schemas in this workspace where the concept is the same — do not invent a second name for an existing concept.
- Every `ft:` term needs `rdfs:label` and `rdfs:comment`.
- Where the research directly supports a claim (e.g. a benchmark from APQC), record the source in `ft:evidence`.
- Output a single JSON-LD file, then a short "REVIEW NOTES" section listing the 5 modeling decisions you are least certain about, so I can review exactly those first.

Do not proceed to blueprint content — schema only. I will review before anything downstream uses it.
```

### 1b. Base ontology — `boblueprint/ft-base-ontology.jsonld`

The schema Bob produces must follow the **Entity / Operation / State** pattern Context Studio expects — a freeform schema.org graph imports but lands in the "empty graph, can't publish" failure mode. The practice base ontology (`boblueprint/ft-base-ontology.jsonld`, validated clean) already models the domain: 10 Entities (ProcessArea, Persona, System, DataObject, PainPoint, Agent, UserBenefit, BusinessBenefit, EvidenceSource, Blueprint), 19 Operations (OwnsProcess, Addresses, EscalatesTo, EvidencedBy, RequiresAccessTo, …), and 10 States (PainPoint, Agent, and Blueprint lifecycles). Two design points to know:

- **`ft:EscalatesTo` (Agent → Persona) is the human-in-the-loop contract in the graph itself** — an Agent invariant requires it before the agent can reach Validated, which is what the Step 3 pressure-test checks.
- **`ft:EvidenceSource` mirrors the harvest `manifest.json`**, so every pain-point and benefit claim stays citable from research through to the client deck.

Bob's per-client job is to **extend** this file (new entities like `ft:RebateClaim`, client enum values, more Operations), never to redesign it. The one-shot prompts in `boblueprint/step1-one-shot-prompts.md` encode this contract.

**Checkpoint 1 (human):** review Bob's "REVIEW NOTES" first, then scan persona names against our persona inventory (Cameron Ortiz, Mara Santos, Peyton Rao, Caleb Owens style). Then run the shape check before Context Studio:

```bash
python boblueprint/validate_ontology.py schemas/{{client}}-v1.jsonld
```

It catches dangling cross-references, duplicate/unprefixed ids, members missing `id`/`type`/`name`, and Operations without `from`/`to`. If it prints problems, paste the list back to Bob with "Fix these validator findings; change nothing else." Import only on a clean exit. Log the review time in `runlog.md`.

---

## Step 2 — Build the graph (ICA Context Studio)

UI steps (consultant-driven — this is deliberately a human checkpoint, not automation):

1. ICA launchpad → **Context Studio** → **New context** → name it `{{client}}-{{process-area}}-v1`.
2. **Import schema** → upload the reviewed JSON-LD from `schemas/`.
3. **Ingest documents** → add the research corpus + interview notes (same files Bob read — the graph grounds what Bob drafted).
4. Let the knowledge graph populate, then use the **built-in AI assistant** to verify: ask it the three grounding questions and check the answers cite the right nodes:
   - "Which personas own {{process area}} and what pain points affect them?"
   - "Which systems does the {{candidate agent}} need access to?"
   - "What evidence supports the {{key pain point}}?"
5. Fix mis-linked nodes in the graph editor; if the same fix recurs, fix the *schema* and re-import rather than patching the graph.

**Checkpoint 2 (human):** graph verified — the three questions return grounded answers. Log it.

---

## Step 3 — Generate + pressure-test the blueprint (ICA agent workflow)

Step 3 runs as an **Agentic App Studio workflow** chaining the two practice agents, with the consultant sign-off gate built into the chain. Build it once during the challenge:

1. **Create the two agents** (each is one of the prompts below saved as an ICA assistant):
   - **Blueprint Generator** — a Process Studio project linked to the Step 2 Context, wrapped as an agent with the generation prompt (3a).
   - **Method Pressure-Tester** — an assistant carrying the pressure-test prompt (3b); no Context binding needed, it reviews whatever draft it receives.
2. **Chain them in Agentic App Studio:** New agentic workflow → add Blueprint Generator → add Method Pressure-Tester consuming the Generator's output → add a **human approval gate** after the Pressure-Tester (the consultant resolves FLAGs and signs off here) → bind the workflow input to the client Context.
3. **Test in Sandbox** before the demo run (AAS supports independent sandbox testing).
4. Optional stretch: expose the workflow as an **A2A endpoint** so other practice tooling can invoke it, and register watsonx Orchestrate as a platform if a run (e.g. Kate's CFO Co-Pilot) needs an Orchestrate agent in the chain. Verify the exact AAS menu paths against the live ICA build — the capabilities shipped across the 26.02–26.04 releases.

Fallback if AAS access isn't available on day one: run the same two prompts manually in Process Studio + an ICA chat assistant — same outputs, the workflow just isn't packaged yet. Don't let the demo block on this.

### 3a. Blueprint Generator prompt

1. **Process Studio** → **New project** → link it to the Context created in Step 2.
2. Run generation with this project prompt:

```text
Using the linked context graph, produce a finance-transformation use-case blueprint for {{process area}} with exactly this structure:

1. COGNITIVE DECOMPOSITION — break the end-to-end process into tasks; classify each as human-retained, agent-assisted, or agent-owned, with a one-line justification tied to a pain point or control requirement in the graph.
2. AGENT REGISTER — for each agent in the graph: name, trigger, inputs (systems + data objects from the graph), actions, outputs, human approval points, and the pain points it addresses.
3. TARGET OPERATING MODEL — how personas' roles change; per persona: 3 user benefits. Then 4 business benefits framed as risk-reduction, cycle-acceleration, governance, scalability.
4. PROCESS NARRATIVE — 3 paragraphs: current state → agents step in → end state. Active voice, present tense, concrete pain-point phrasing.

Use only entities that exist in the context graph. Where the graph lacks something the structure requires, emit a "GAPS" list instead of inventing content.
```

### 3b. Method Pressure-Tester prompt

3. **ICA pressure-test** — the second agent in the workflow runs the method check against the draft:

```text
Pressure-test this blueprint against IBM's finance-transformation method:
- Does every agent have a defined human approval point? Flag any that don't.
- Are the business benefits traceable to pain points with evidence in the graph?
- Is any agent-owned task one that IBM method says must stay human-retained (e.g. judgment-based accounting estimates, final journal approval)?
- Does the decomposition cover the full APQC scope of {{process area}}, or are sub-processes missing?
Return: PASS/FLAG per check, with the specific fix for each FLAG.
```

**Checkpoint 3 (human):** this is the workflow's built-in approval gate — resolve every FLAG (accept the fix or justify the deviation in `runlog.md`), then sign off; the workflow releases the blueprint and exports it to `blueprints/`.

---

## Step 4 — Render the deck (IBM Bob)

```text
Render the attached blueprint export into a client-ready first-draft deck in our standard finance-transformation format.

STRUCTURE (one section per item):
1. Title + engagement context
2. Process narrative (the 3 paragraphs — one slide each: current state / agents step in / end state)
3. Personas (named, with role and top pain points)
4. Pain points → agents mapping (one slide per agent from the agent register)
5. User benefits by persona (3 per persona)
6. Business benefits (4: risk-reduction, cycle-acceleration, governance, scalability)

STYLE RULES:
- IBM-branded PPTX template from our practice assets — do not restyle it.
- Active voice, present tense. Concrete pain-point phrasing ("Manual capitalization decisions create delays and misclassification risk." — never "There are some manual issues.").
- Benefits framed by stakeholder role; nothing invented beyond the blueprint. If a slide needs content the blueprint lacks, insert a [SENIOR REVIEW] marker instead.

Output the PPTX plus a one-paragraph summary of every [SENIOR REVIEW] marker you inserted.
```

**Checkpoint 4 (human):** senior consultant reviews the deck, especially the `[SENIOR REVIEW]` markers. Stop the timer here — this is the "under an hour" number for the demo.

---

## Agents in this submission — what gets built vs. designed

Three layers, so the team answers this consistently:

1. **Designed, not built (the deliverable):** the blueprint's agent register — Jo's Finance Resolution Agent, Kate's CFO Co-Pilot, and every `ft:Agent` in the ontology — are target-state *client* agents specified on paper with governance contracts (`ft:EscalatesTo` invariant). Deployment is the client engagement's job, not the challenge's.
2. **Used, not built:** Bob is the agentic executor of the pipeline itself. No custom orchestrator is needed — and staying agent-light matches the 2026 criteria (everyday usage over solution builds).
3. **Built during the challenge (small, deliberate):** two ICA agents chained in an **Agentic App Studio workflow** —
   - **Blueprint Generator** — the Step 3a generation prompt as an agent, bound to the client Context;
   - **Method Pressure-Tester** — the Step 3b PASS/FLAG method-check prompt as an agent;
   - chained Generator → Pressure-Tester → **human approval gate**, so the consultant sign-off is a structural part of the workflow, not a habit.

   Setup steps are in Step 3 above. The agents also supply the `assistantId` values the automation script below requires. Note the no-code chat Agent Builder has no multi-agent support — the chain must be built in AAS. Post-challenge roadmap: expose the workflow as an A2A endpoint and add watsonx Orchestrate agents (e.g. for Kate's CFO Co-Pilot execution leg) via AAS platform integration.

## Optional — API automation (Python, ICA REST API)

For the stretch goal (templating the workflow), Steps 3's pressure-test and other prompt executions can be scripted against the ICA API so a junior consultant runs the whole pipeline from one script. Conventions below were verified against the May 2026 Knowledge Center export — **confirm against the live Swagger before the demo** (`https://servicesessentials.ibm.com/apis/docs/swagger-ui/index.html`).

⚠️ Note: the `ica-api` skill bundled in `consulting-claude-code-skills` is stale — it gives the wrong host (`consultingadvantage.ibm.com`) and wrong path prefix (`/api/v1/`). Use the conventions below.

```python
import os
import requests

# Global host; regional alternative: https://<region>.ica.ibm.com/ica  (region: us, uki, remea, au, canada, japan, india, sg)
ICA_HOST = "https://servicesessentials.ibm.com"
API_KEY = os.environ["ICA_API_KEY"]  # ICA -> Settings -> My Settings -> API Keys (shown once)
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def list_assistants(limit=20):
    r = requests.get(f"{ICA_HOST}/apis/v3/assistants", headers=HEADERS, params={"limit": limit})
    r.raise_for_status()
    return r.json()


def execute_prompt(assistant_id, prompt, collection_id=None, chat_id=None):
    """Run one pipeline prompt (e.g. the pressure-test) against an ICA assistant.
    collection_id points at the document collection holding the blueprint export."""
    body = {"assistantId": assistant_id, "prompt": prompt}
    if collection_id:
        body["collectionId"] = collection_id
    if chat_id:
        body["chatId"] = chat_id  # keeps multi-turn review context
    r = requests.post(f"{ICA_HOST}/apis/v3/executePrompt", headers=HEADERS, json=body)
    r.raise_for_status()
    return r.json()


def upload_to_collection(file_path, collection_name):
    """RAG upload — put the blueprint export / research corpus into a document collection."""
    # See /apis/v3/document_collections in Swagger for the exact multipart contract.
    raise NotImplementedError("Wire to POST /apis/v3/document_collections per live Swagger")


if __name__ == "__main__":
    agents = list_assistants()
    print([a.get("name") for a in agents.get("data", agents)])
```

Two notes for the stretch phase (post-challenge, verify in the live build):
- **Agentic App Studio (AAS)** now supports A2A agents and watsonx Orchestrate as a platform — if the accelerator ever needs to call an Orchestrate agent (e.g. Kate's Run 2 execution step), register it in AAS rather than hand-building an adapter.
- Multi-agent orchestration lives in AAS; the no-code chat Agent Builder has no collaborator support.

---

## Run log template (`runlog.md`) — the judging evidence

```markdown
# Run {{n}} — {{client scenario}} — {{date}}

| Step | Start | End | Minutes | Checkpoint decision |
|---|---|---|---|---|
| 1. Schema draft (Bob)          |  |  |  | edits made: … |
| 2. Graph build + verify (ICA)  |  |  |  | grounding Qs passed: y/n |
| 3. Blueprint + pressure-test   |  |  |  | FLAGs resolved: … |
| 4. Deck render (Bob)           |  |  |  | [SENIOR REVIEW] markers: … |
| **Total** |  |  |  | vs. hand-built baseline: {{hours}} |
```

Fill this for both demo runs (Jo's exception orchestrator, Kate's CFO co-pilot) **and** for the hand-built baseline — the before/after table is the core of the judged result.
