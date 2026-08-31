# Where files hide inside files

Reference for `deep-extract`. Each section says where embedded content lives,
what the extractor does with it, and what it cannot do — so "not in the output"
can be told apart from "not supported".

---

## 1. OOXML — .docx / .xlsx / .pptx (and the macro-enabled variants)

A zip. Embedded files are ordinary zip entries:

| Location | Holds |
|---|---|
| `word/embeddings/*` | embedded Word/Excel/PowerPoint documents, and `oleObject*.bin` |
| `xl/embeddings/*`, `ppt/embeddings/*` | same, for workbooks and decks |
| `word/media/*`, `xl/media/*`, `ppt/media/*` | images, including the EMF/WMF *preview* of each embedded object |
| `docProps/{core,app,custom}.xml` | author, company, timestamps, sensitivity labels |

Each embedding is wired into the body through a relationship:

```xml
<w:object>
  <v:shape><v:imagedata r:id="rId7"/></v:shape>          <!-- the icon -->
  <o:OLEObject ProgID="Word.Document.12" r:id="rId8"/>   <!-- the payload -->
</w:object>
```

`rId8` resolves via `word/_rels/document.xml.rels` to the part in
`word/embeddings/`. The extractor emits `⟦EMBEDDED OBJECT⟧` at that point in
the text, so position in the narrative is preserved.

**ProgID tells you what to expect.** `Word.Document.12` → a real `.docx`.
`Excel.Sheet.12` → a real `.xlsx`. `Package` → an `oleObject*.bin`, which is an
OLE compound file wrapping an arbitrary file (§2) — very often a `.msg`.

**Declared vs present.** Relationships and parts are independent. A damaged or
partially-synced package can declare an embedding whose part is absent. The
extractor diffs the two and reports the gap; this is the single most useful
signal it produces.

**Extracted:** body text in document order, tables as rows, headers/footers,
footnotes/endnotes, comments with author and date, tracked insertions and
deletions, hyperlink targets, image alt text, text boxes, `w:sdt` content
controls, all document properties.

**Not extracted:** field *results* that Word never cached, VBA source in
`vbaProject.bin` (the binary is saved, not decompiled), OOXML chart series
values (the chart XML is saved), ink annotations.

### The 1,048,576-row problem

Excel writes a `<row>` for every formatted row, so a sheet holding 400 real
values can be a 130 MB XML part. Worksheets are stream-parsed with per-row
clearing, and only rows carrying content are emitted. A sheet that produces a
few kilobytes from a huge part is normal, not a failure — check `<v>` counts
before suspecting loss.

---

## 2. OLE compound files — .doc / .xls / .ppt / .msg / oleObject*.bin

Magic `D0 CF 11 E0 A1 B1 1A E1`. A little FAT filesystem of streams.

| Stream | Holds | Handling |
|---|---|---|
| `\x01Ole10Native`, `Package` | an arbitrary embedded file with its original name | unwrapped, then re-dispatched |
| `CONTENTS` | Visio/Equation and similar payloads | passed through if it carries a known magic |
| `WordDocument` + `0Table`/`1Table` | Word 97-2003 | text via the piece table |
| `Workbook` / `Book` | Excel 97-2003 | BIFF8 shared-string table + label cells |
| `PowerPoint Document` | PowerPoint 97-2003 | TextBytes/TextChars atoms |
| `__substg1.0_*` | Outlook `.msg` properties | subject/from/to/cc/sent/headers/body |
| `__attach_version1.0_#N/__substg1.0_37010102` | attachment bytes | named from `3707001F`, re-dispatched |
| `\x01CompObj` | the ProgID string | reported |

### Ole10Native layout

`DWORD` total size · `WORD` flags · ASCIIZ label · ASCIIZ original path ·
`DWORD` unknown · `DWORD` temp-path length + path · `DWORD` payload size ·
payload. If the header does not parse, the extractor scans the first 4 KB for a
`PK`/`%PDF`/`{\rtf`/CFB magic and cuts from there.

**Limits.** Legacy `.doc` fast-saved with an unusual piece table may yield
partial text; `.xls` shared strings spilling across `CONTINUE` records are read
to the first spill boundary; a `.msg` **attached to another .msg** is a nested
*storage*, and its text fields are read in place but it is not re-serialised
into a standalone `.msg` file. Encrypted OLE (`EncryptedPackage`) is saved but
not decrypted.

---

## 3. PDF

Attachments live in the catalog's `/Names /EmbeddedFiles` tree and in
`FileAttachment` annotations. Both are pulled and re-dispatched.

Page text needs `pypdf`. **A scanned PDF yields nothing** — the extractor
warns when every page comes back empty, which means OCR is required. It does
not OCR.

---

## 4. Email — .eml

Parsed with the stdlib `email` package. Headers, every `text/plain` and
`text/html` body part, and every part with a filename, which is re-dispatched.

---

## 5. Damaged and truncated containers

A zip's index lives at the *end* of the file, so a short download loses the
index and every standard reader reports "not a zip file" for an otherwise
mostly-intact archive.

The extractor falls back to walking local file headers from offset 0 — each
entry carries its own name, compression method and sizes — and recovers
everything up to the break. It reports:

- how many bytes the container is short,
- which entry was cut,
- and (via §1's reconciliation) which embeddings were lost entirely.

Entries after the break are unrecoverable from that copy. Re-download from the
source; on a synced drive (Box, Drive, OneDrive) confirm the file is fully
hydrated first — a file can lack the `Offline` attribute and still be short.

---

## 6. Output layout

```
_ALL_TEXT.md      all text, whole tree, in order
_TREE.txt         size · kind · nesting · [dup of …] · [status]
_MANIFEST.json    path, sha1, kind, saved_as, text_file, missing_embeddings
files/            recovered binaries        (container children under  name~/ )
text/             per-node text             (same  name~/  convention   )
```

The `~` suffix keeps a container's *directory* of children from colliding with
the *file* holding the container itself. Path components are truncated to 100
characters and de-duplicated with a `__2` suffix, so a long name in `files/`
may be shorter than the same node's `path` in `_MANIFEST.json` — the manifest
is authoritative.

Identical bytes appearing at two points in the tree are extracted at both and
cross-referenced with `duplicate_of`; nothing is silently dropped.

---

## 7. Memory

Every entry of a container is decompressed into memory at once. A 28 MB
workbook that expands to 283 MB is real and observed. Worksheet XML is
streamed, which removes the dominant cost, but very large containers still
need headroom proportional to their *uncompressed* size.
