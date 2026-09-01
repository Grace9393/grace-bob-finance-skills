---
name: deep-extract
description: Recursively extract the full content of a document — including the files embedded inside it. Pulls body text, tables, headers/footers, footnotes, comments, tracked changes and properties out of docx/xlsx/pptx/pdf, then descends through embedded objects, .msg attachments and package streams to a bounded depth (8 levels by default, set with --max-depth), recovering readable entries from damaged containers. Use when the user asks to extract, read, dump, unpack, mine or "get everything out of" a document, mentions embedded/attached/nested files, icons inside a Word file, attachments inside attachments, an SOP or procedure doc with objects in it, or when a document must be reviewed in full and the visible text is only part of it.
---

# Deep extract — conduct guide

A Word file that shows three little Word icons is three more documents, each of
which may hold an email, which may hold a spreadsheet. Reading only the outer
body text is reading a fraction of the material. This skill takes the whole tree.

**This skill also holds the shared extraction engine.** `scripts/deep_extract.py`
is the single implementation of container parsing across the skill set;
`contract-review` and `corpus-prep-for-ingestion` import it through
`scripts/_engine.py` rather than carrying their own parsers. Fix a parsing bug
here and it lands in all three. Keep `__version__` accurate — consumers check it
against their `MIN_VERSION`.

## Step 1 — Run it

```
python scripts/deep_extract.py "path/to/file.docx" -o extracted/
```

Always point `-o` at an **empty** directory. The script never deletes, so a
reused directory mixes runs; it warns when it detects one.

Useful flags: `--max-depth N` (default 8) · `--no-media` (catalogue images
without writing them) · `--max-text-mb N` (cap the consolidated file only) ·
`--quiet`.

Exit code `0` clean, `2` completed **with warnings** — 2 is not failure, it
means read the warnings.

## Step 2 — Read the warnings before the content

Warnings are printed last and repeated in `_ALL_TEXT.md` and `_MANIFEST.json`.
Three of them change what you may conclude:

| Warning | What it means | What you must do |
|---|---|---|
| `central directory unusable … salvaging` | container is damaged; entries recovered by walking local headers | say the source is damaged; the entry list may be incomplete |
| `TRUNCATED: entry X needs N bytes` | the file is physically short | report the shortfall in bytes and ask for a re-download |
| `N embedded file(s) are referenced but absent` | the document **declares** embeddings whose parts are gone | list them by name — this is content the user does not have |

That last check is the one that matters most. A package can reference 42
embedded objects and physically contain 29; extracting the 29 silently would
misrepresent the document as complete.

## Step 3 — Navigate the output

| Path | Use it for |
|---|---|
| `_ALL_TEXT.md` | every text unit in the whole tree, in order — read this first |
| `_TREE.txt` | one line per node: size, kind, nesting, duplicate flags |
| `_MANIFEST.json` | machine-readable — path, sha1, kind, saved_as, text_file, warnings |
| `files/` | every recovered binary, openable directly in Word/Excel/Outlook |
| `text/` | per-node text, mirroring the tree |

In `files/` and `text/`, a container's children live in a sibling directory
whose name carries a `~` suffix — `oleObject2.bin` is the file,
`oleObject2.bin~/` holds what was inside it.

## Step 4 — Report to the user

Lead with the shape of the tree, not the text: *"the 65 MB docx contains 24
embedded Word documents, 3 workbooks and 4 Outlook messages; two of those
emails carry their own .docx and .pptx attachments."* Then the warnings. Then
the content.

Always give the absolute output path.

## What the markers in the text mean

| Marker | Meaning |
|---|---|
| `⟦EMBEDDED OBJECT progid=… -> part⟧` | an embedded file sits at this exact point in the narrative |
| `[IMAGE: part]`, `[IMAGE ALT-TEXT: …]` | picture and its alt text |
| `{+inserted+}`, `{-deleted-}` | tracked changes |
| `⟦COMMENT n by author (date): …⟧` | reviewer comment, anchored in place |
| `<mailto:…>`, `<file://…>`, `<http…>` | hyperlink target after its link text |
| `\| a \| b \|` | table row |

The `⟦EMBEDDED OBJECT⟧` markers are what let you say *where* an attachment
belongs — "the credit-note template is embedded in the ZCRQ row of Block 1",
not just "there is a template somewhere in the file".

## Gates

- **Never claim a document is fully extracted while warnings are outstanding.**
  Quote the warning instead.
- **Count before asserting.** The declared-vs-recovered table gives the true
  denominator; use it rather than counting what landed in `files/`.
- **Duplicates are flagged, not removed.** `[dup of …]` in `_TREE.txt` means
  the same bytes appear twice — often the same attachment embedded in both the
  parent and a child. Do not report it as two distinct documents.
- **Scanned PDFs produce no text.** The script says so; it does not OCR.
- Formats and their limits are in `references/container-formats.md` — check it
  before concluding that content is missing rather than merely unsupported.
