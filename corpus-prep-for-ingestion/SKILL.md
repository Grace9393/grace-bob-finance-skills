---
name: corpus-prep-for-ingestion
description: Make a document corpus ingestible by a platform with file-size caps — extract documents embedded inside Word and Excel containers, settle duplicates by hash rather than by reading, reduce oversized files to text with a loss log, and verify the result. Use when a corpus is about to be uploaded to IBM Process Studio, Context Studio, a RAG pipeline or any ingestion surface with per-file or total-size limits; when a .docx or .xlsx may contain embedded documents; when an upload is rejected for size; or when preparing SOPs for analysis and you need to know what the platform will never see.
---

# Corpus prep for ingestion

A container-aware extraction and reduction pass. It does **not** analyse, summarise or
design anything. It makes a corpus uploadable and tells you what would otherwise be
invisible.

Run it before the ingestion platform, never instead of it.

## The problem it solves

A `.docx` is a ZIP. Word stores whole documents embedded inside it under
`word/embeddings/` as `.docx` / `.xlsx` / `.bin` parts. Those are **separate documents**,
not formatting. An ingestion platform sees one file; the corpus contains many.

Worked example, measured:

| | |
|---|---|
| Corpus | 26 standalone files, 91.9 MB |
| Containers holding embedded parts | **5** — and two of them are under 5 MB |
| Embedded parts | **34** — 22 docx · 5 xlsx · 7 OLE bin |
| Byte-identical duplicates of a standalone file | 12 |
| **Parts with no standalone counterpart** | **22** |
| Files over a 10 MB per-file cap | 2 before extraction, 2 after |

The largest file was 61.4 MiB against a 10 MB cap — **six times over, and unuploadable**.
Inside it was a 269 KB workbook holding a 583-account portfolio with personal data, last
updated six years earlier, reachable no other way.

## Four rules — each cost a failed run to learn

**1 · Never read a document to decide something a hash can decide.**
Duplicates are settled by SHA-256. Same hash, same bytes, definitively duplicate.
Different hash means the bytes differ — it does **not** mean the meaning differs. Never
upgrade "different hash" to "unique content", never downgrade it to "duplicate".

A first attempt at this task required reading both copies to judge similarity. It pulled
70 MB of documents into the agent context, hit the limit at 90%, and wrote none of its
four deliverables.

**2 · Write the manifest first, and flush it incrementally.**
Metadata and hashes come from the ZIP central directory. A run that stops halfway must
leave a usable manifest on disk. A complete manifest held in context is worth nothing.

**3 · Open every container, not just the obvious one.**
In the worked example, four of the five containers holding embedded documents were
ordinary-looking files, two under 5 MB. Filtering by size finds none of them.

**4 · Never truncate silently.**
Every reduction gets a row in `dropped.md` naming what was lost — media count, formulas,
formatting. A reduced file with no loss record is a corpus with an undocumented hole.

**5 · A container that will not open is a finding, not a skip.**
Container parsing is delegated to the shared engine in the **`deep-extract`** skill,
which must be installed in the same skills directory. An earlier version of this script
caught the exception and moved on: handed a damaged 65 MB SOP holding 29 embedded
documents, it reported `embedded_parts: 0` and exited 0 — a clean, confident, wrong
answer, and the exact failure rule 4 exists to prevent. Damage now lands in
`summary.json` under `damaged_containers`, and parts the container names but does not
hold land under `declared_but_absent`.

When either is non-empty, **every count in the manifest is a floor, not a total.** Say so
when reporting; do not present the corpus as fully inventoried.

## Running it

```bash
python scripts/corpus_prep.py inventory --in <CORPUS> --out <OUT> [--cap-mb 10]
python scripts/corpus_prep.py extract   --in <CORPUS> --out <OUT>
python scripts/corpus_prep.py fit       --out <OUT> [--cap-mb 10]
python scripts/corpus_prep.py check     --in <CORPUS> --out <OUT> [--cap-mb 10]
```

`inventory` and `extract` need the `deep-extract` skill for the shared engine.
`fit` additionally needs `python-docx` and `openpyxl`.

Output:

| Path | Contents |
|---|---|
| `corpus-manifest.md` · `manifest.csv` | one row per standalone file and per embedded part — bytes, hash, over-cap flag, duplicate-of; plus sections for damaged containers and referenced-but-absent parts |
| `summary.json` | the totals, plus `damaged_containers` and `declared_but_absent` |
| `extracted/` | embedded parts as standalone files, named `<container>__<part>` |
| `upload-ready/` | the final set that fits the caps |
| `dropped.md` | every reduction and what it lost |

## Platform caps

Defaults are IBM Process Studio's SOP scan. Change `--cap-mb` for anything else.

| Platform | Per file | Total | Count |
|---|---|---|---|
| **Process Studio** SOP scan | 10 MB | 500 MB | 2000 |
| **Context Studio** ingestion | — | 100 MB per batch | 30 per batch |

These are different limits for different products. Do not conflate them: a corpus that
fits Process Studio may still need splitting for Context Studio.

## What this skill must not do

- No atomic steps, no agents, no autonomy zones, no process description. That belongs to
  the design tool downstream, and pre-empting it is how a prep pass turns into a
  competing blueprint.
- No content-derived filenames. Mechanical names are traceable and free; readable names
  cost a full read of every file.
- No summarising a document in place of extracting it.
- No modification of the source corpus. It is read-only, and `check` verifies it.

If you find yourself writing a sentence about what a process *does*, stop — wrong tool.

## Reading text at all

Exactly one situation justifies it: classifying ingestion risks. Cap it at the **first
4,000 characters** of each file — enough for a title, a document-control block, a review
date and a heading list.

Risks worth surfacing, all answerable within that cap:

| Risk | Why it matters downstream |
|---|---|
| Empty extraction | a scanned diagram or OLE object with no text — the platform will ingest silence |
| Terminology drift | `AP` and `Accounts Payable` as separate entities is the documented cause of duplicate knowledge-graph nodes |
| Stale sources | a review or effective date older than 24 months, quoted |
| Personal data | names, emails, account-level data — decide before upload, not after |

If a risk cannot be assessed within the cap, write `not assessed within cap`. An honest
gap costs nothing; a context stop costs the run.

### Empty extraction is not grounds for exclusion

**Keep text-free files in `upload-ready/`**, flagged as text-free. Let the ingesting
platform decide.

A file yielding no text is often a **diagram** — a process map, a swimlane, a decision
tree — which is exactly what a process-analysis engine most wants. Process Studio's SOP
scan has an optional **Vision** phase that describes embedded PDF and PPTX images at
~216 DPI. Excluding the file guarantees the diagram is never seen; including it gives
Vision a chance.

Exclude only what **cannot be uploaded** — over the cap and irreducible. Never exclude
something merely because this pass could not read it. That is a decision for the platform,
not for the prep step.

## Report exactly five numbers, and label the units

**standalone files · embedded parts · containers holding parts · byte-identical
duplicates · parts with no counterpart.**

State MiB or MB and use one convention throughout. A summary mixing 64.4 MB (decimal) with
91.9 MiB (binary) in the same table is the kind of error nobody catches and everybody
quotes. Cross-check every number in the prose against `summary.json` before writing it —
in the reference run the artifacts were correct and three figures in the narrative were
not.

## Verifying

`check` asserts: manifest and `dropped.md` exist · at least one container was opened ·
no `upload-ready` file exceeds the cap · total and count within limits · every
`duplicate_of` is hash-backed by construction. It exits non-zero on failure.

Report five numbers, always: **standalone files · embedded parts · containers holding
parts · byte-identical duplicates · parts with no counterpart.** The last one is the
finding — it is the count of documents the platform would never have seen.

## Related

- `ica-process-studio` — the design tool this feeds. It is a conduct guide, not a file
  utility; the caps above are documented there too.
- `ica-context-studio` — the other ingestion surface, with different limits.
