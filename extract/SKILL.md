---
name: extract
description: One entry point for getting content out of documents, in whichever shape the task needs — a full recursive dump including files embedded inside files, a contract reviewer's body/comments/flags set, or a corpus made ingestible under a file-size cap. Use whenever the user wants to extract, read, dump, unpack or mine a document and it is not yet obvious which depth or output shape they need, or when they ask for extraction generally rather than naming a specific tool.
---

# Extract — conduct guide

Three extraction jobs come up repeatedly and they want different outputs, not
different parsers. This skill is the single entry point that routes to the right
one.

**It contains no extraction logic of its own.** Each profile runs the script in
the skill that owns it, so there is exactly one implementation of each behaviour
and a fix there takes effect here immediately:

| Profile | Runs | Owning skill |
|---|---|---|
| `deep` | `deep_extract.py` | `deep-extract` |
| `contract` | `contract_extract.py` | `contract-review` |
| `corpus` | `corpus_prep.py` | `corpus-prep-for-ingestion` |

Those skills must be installed in the same skills directory. Run
`python scripts/extract.py where` to see what resolved — do that first whenever a
profile reports a missing skill.

## Step 1 — Pick the profile

Ask what the output is *for*, not what the file is.

| The user wants… | Profile |
|---|---|
| everything the document contains, including embedded attachments and their attachments | `deep` |
| to review a contract before signature | `contract` |
| to upload a document set to a platform with a per-file cap | `corpus` |
| a document read properly *and* checked for signature hygiene | `all` |
| not sure yet | `deep` — it is the superset; narrow afterwards |

```bash
python scripts/extract.py deep     "path/to/file.docx" -o extracted/
python scripts/extract.py contract "path/to/contract.docx" -o extracted/
python scripts/extract.py corpus   inventory --in CORPUS --out OUT
python scripts/extract.py all      "path/to/contract.docx" -o extracted/
```

`corpus` runs in order: `inventory` → `extract` → `fit` → `check`.

Flags not listed above are passed straight through to the underlying script, so
`deep`'s `--max-depth`, `--no-media`, `--max-text-mb`, `--quiet` and `corpus`'s
`--cap-mb` all work unchanged.

## Step 2 — Read the exit code before the content

Uniform across every profile:

| Code | Meaning |
|---|---|
| 0 | clean |
| **2** | **finished with warnings** — damaged container, embedded parts referenced but absent, or content reduced |
| 1 | failed |

**2 is not success.** It means the extraction is real but incomplete, and the
gap is described in the output. Never report a document as fully extracted while
a 2 is outstanding — quote the warning instead.

## Step 3 — Report the shape before the text

Lead with what the document turned out to *be*: how many embedded files, how
deep the nesting went, what is missing. A 65 MB Word file that holds 24 embedded
documents and 4 Outlook messages is a different object from a 65 MB report, and
the user needs to know which they have before reading any of it.

Then hand over the absolute output path.

## Gates

- **Do not narrow the profile for the user.** If they asked for everything, run
  `deep`; `contract` and `corpus` both discard material by design.
- **Embedded attachments are content.** `contract` lists them but does not read
  them. If they matter to the conclusion, run `deep` as well (or use `all`).
- **A count is only a total when the exit code is 0.** With warnings present,
  every count is a floor.
- Per-profile detail lives in the owning skill's SKILL.md; format internals are
  in `deep-extract/references/container-formats.md`.
