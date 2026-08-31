---
name: nestle-ap-ta-review
description: Use when reviewing a new version of the Nestlé AP Transformation Transaction Agreement — runs the RACI audit, extracts contract text, annotates the .docx with IBM review comments, and produces a findings report. Triggers on phrases like "review the new TA draft", "run the contract review", "annotate the TA", "audit the RACI", or "check the new version".
metadata:
  argument-hint: "[path to new .docx draft]"
---

# Nestlé AP Transformation TA — Review Workflow

Follow these steps in order whenever a new draft of the Transaction Agreement arrives.

## Step 0 — Locate inputs

Ask the user (using `ask_followup_question`) for:
1. **The path to the new .docx draft** (absolute path, e.g. `C:\...\AP TA v5.0 DRAFT.docx`)
2. **The version label** (e.g. `v5.0`) — used in output file names and report headers

If the user has already provided these in the message, skip the question.

---

## Step 1 — Extract contract text

Run `pptx_extract.py` only if a new **proposal deck** accompanies the draft (the user will say so).
For a TA-only review, skip to Step 2.

```
python scripts/pptx_extract.py "<path to .pptx>" > scripts/valueprop_new.txt
```

---

## Step 2 — Extract body text from the new .docx

Use `python-docx` via a one-liner to dump paragraph text for diff and line-number reference:

```powershell
python -c "
from docx import Document
d = Document(r'<DRAFT_PATH>')
import io
lines = [p.text for p in d.paragraphs]
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                lines.append(p.text)
io.open('scripts/contract_text_new.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('Paragraphs written:', len(lines))
"
```

Save as `scripts/contract_text_new.txt`.

---

## Step 3 — Run the RACI audit

Run [`raci_audit.py`](scripts/raci_audit.py) against the **new** text file. Update the line-number
constants at the bottom of the script (`w1 = rows(...)`, `w2 = rows(...)`) if the RACI tables have
shifted — confirm with the user before editing.

```powershell
cd "H:\My Drive\AA\Nestle-AP-TA-review"
python -c "
import io, re, sys
# quick search for RACI table boundaries
L = io.open('scripts/contract_text_new.txt', encoding='utf-8').read().split('\n')
for i, line in enumerate(L, 1):
    if 'Wave 1' in line and 'RACI' in line.upper():
        print('Wave 1 RACI near line', i, ':', line[:80])
    if 'Wave 2' in line and 'RACI' in line.upper():
        print('Wave 2 RACI near line', i, ':', line[:80])
"
```

Then run the audit:

```powershell
python scripts/raci_audit.py 2>&1 | Tee-Object scripts/raci_audit_output.txt
```

Review flags for:
- `DUAL-ACCOUNTABLE` / `NO-ACCOUNTABLE`
- `OUTCOME-TARGET on SUPPLIER-R` (highest risk)
- Any new initiatives or ID changes vs the previous version

---

## Step 4 — Compare against known findings

Read the **master findings list** (`AP-TA-merged-master-list.html`) and the previous version's
notes (e.g. `scripts/v4_notes.json`) to identify which findings have been resolved, which persist,
and which are new.

Create a new notes file for this version:

```powershell
copy scripts\v4_notes.json scripts\v5_notes.json   # adjust version numbers
```

Edit `scripts\v5_notes.json` to mark each finding as:
- `"status": "resolved"` — clause is fixed
- `"status": "persists"` — same issue in new draft
- `"status": "new"` — issue not present in previous version
- `"status": "regressed"` — was resolved, now back

---

## Step 5 — Strip any stale comments from the draft

If the incoming .docx already carries comments from a previous review round, clean it first to
avoid disclosure of internal notes to the client:

```powershell
python scripts\strip_comments.py "<DRAFT_PATH>" -o "<DRAFT_PATH_CLEAN>"
```

Use the `_clean` version as the source for Step 6.

---

## Step 6 — Annotate the new draft

Open `scripts/annotate.py` and:
1. Update `SRC` to point to the clean draft from Step 5
2. Update `DST` to a sensible output path (e.g. `...\AP TA <VERSION> - REVIEW ANNOTATED.docx`)
3. Review the `NOTES` list — remove comments for resolved findings, add new ones for new findings,
   update snippet text if clauses have moved

Then run:

```powershell
python scripts\annotate.py
```

Confirm the output: `Comments attached: N` should equal the number of active findings. Any entries
in `NOT ANCHORED` mean a snippet no longer exists verbatim — update `annotate.py` with the new
clause text.

---

## Step 7 — Generate the review report

Use the `contract-review` skill (type `/contract-review`) with the new draft as input to produce a
structured HTML findings report. Reference:
- `scripts/contract_text_new.txt` for quoted clause text
- `scripts/raci_audit_output.txt` for RACI evidence
- `scripts/v5_notes.json` for status of each finding vs prior version

Save the output as `AP-TA-<VERSION>-review.html` in the project root.

---

## Step 8 — Pre-signature hygiene check

The `scripts/review_flags.md` file documents known placeholder patterns from v1.0. Run a quick
scan of the new draft for unresolved hygiene issues:

```powershell
python -c "
from docx import Document
d = Document(r'<DRAFT_PATH>')
import re
patterns = [r'XXXX', r'\[.*?\]', r'TBC\b', r'TBD\b', r'_{4,}', r'N/A']
for i, p in enumerate(d.paragraphs, 1):
    for pat in patterns:
        if re.search(pat, p.text):
            print('Para %d [%s]: %s' % (i, pat, p.text[:120]))
            break
"
```

Any hits that are not intentional `[N/A]` entries should be flagged in the report.

---

## Step 9 — Summarise delta from prior version

Produce a concise delta note for the project leader. Format:

```
## Changes v<PREV> → v<NEW>
### Resolved
- <list>
### Persisting
- <list>
### New findings
- <list>
### Regressed
- <list>
```

Save this as `scripts/v<NEW>_notes.json` and include it in the HTML report header.
