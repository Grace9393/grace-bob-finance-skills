---
name: ask-finance-grounded
description: Conduct the client-specific "Ask Finance" workflow — sanitize finance documents, build a governed corpus, answer questions cite-or-refuse from that corpus only, and gate quality with the golden-question eval. Use when the user mentions Ask Finance, grounded finance Q&A, cash/DSO/close questions against client data, data sensitivity for AI, or watsonx Challenge proposal 05.
---

# Client-specific Ask Finance — conduct guide

You (Bob) are conducting a governance-first grounded Q&A workflow. The prime rule, which you also obey when answering directly: **answer ONLY from the governed corpus, cite document + figure for every claim, and refuse with "what data is missing" when the corpus can't support an answer. Generic financial advice is a failure, not a fallback.**

## Step 1 — Sanitize (before anything moves)

```
python scripts/askfinance.py sanitize --in raw/ --out clean/
```
Report redaction counts per file and tell the data owner to spot-check. Accounts, IBANs, emails, phones, and byline names are scrubbed; business figures stay. (Production path: the client's DLP tool replaces the regex scrubber.)

## Step 2 — Build the grounded surface

- **Tier A (no ICA key):** `python scripts/askfinance.py pack --dir clean --q "<question>"` → `grounded_prompt.txt` bundles the corpus + cite-or-refuse rules + question. Run it yourself, or paste into an ICA assistant.
- **Tier B (ICA key set):** `upload --dir clean --name <collection>` then `ask --collection <id> --q "..."` (or the UI-uploaded collection + assistant).

## Step 3 — Answer

Whether via `pack` or a collection: three levers/causes maximum per answer, each cited `[document]`, ranked by financial impact. If the user asks something the corpus can't support (forecasts, other periods, other entities): refuse per the prime rule — name exactly what's missing.

## Step 4 — Eval gate (before any demo or distribution)

```
python scripts/askfinance.py eval --collection <id>              # live
python scripts/askfinance.py eval --canned answers.json          # offline, manually-collected answers
```
The golden set includes a question that MUST be refused. Gate: ≥ 80%. If it fails, read the failures, tune the assistant/system prompt, re-run. **Report scores honestly: an offline/canned score is labeled offline; only a live-assistant run is "the grounding score."**

## Guardrails
- Never move raw (unsanitized) documents anywhere, including into your own context beyond what sanitization requires.
- Per-role surfaces: CFO and analyst get separate collections/assistants — don't merge them for convenience.

## Metric to capture
The live grounding score vs. the 80% gate, redaction counts, and one on-camera refusal, logged in `runlog.md`. Full context: `references/proposal.md`; demo flow: `references/video-script.md`.
