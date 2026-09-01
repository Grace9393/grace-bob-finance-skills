---
name: exec-diagnostic-onepager
description: Convert long analysis documents into a one-page executive diagnostic that argues Problem → Pain points → Root causes → Solution, with one named spine running through all four parts, every block cited to the document it came from, and scripts that prove nothing was dropped from the sources, nothing was invented, the parts line up and it fits one printed page. Use when a stakeholder asks for a one-pager, an executive summary, a "put the finger on the wound" page, a synthesis of several reports, or says a draft is "too focused on the roadmap" and wants the diagnosis foregrounded.
metadata:
  argument-hint: "[the source documents, and who the one-pager is for]"
---

# Executive diagnostic one-pager — conduct guide

A senior reader does not want the roadmap first. They want to know what is
broken, how badly, why it stays broken, and only then what you propose. The
order is the argument, and getting it wrong is the most common reason a
well-researched page lands flat.

This skill converts a pile of analysis into that page and then proves the page.
The proving is most of the value: compression is safe, silent loss is not, and
neither the writer nor the reader can spot the difference unaided.

Use `ibm-carbon-report` for how the page **looks**. This is about what it
**says** and how you know it is true.

---

## The shape

Four parts, in this order, and no other:

| # | Part | Job | Length |
|---|---|---|---|
| 1 | **Problem statement** | one paragraph; the single fact the reader must leave with, and the names of the threads to come | 4–6 lines |
| 2 | **Pain points** | the most important part of the page; what is actually wrong, with specifics | the largest block |
| 3 | **Root causes** | why each pain persists; one cause per pain, same order | compact |
| 4 | **Solution** | brief, and last | smallest block |

Part 2 gets the most space. If the solution is the biggest block, the page is a
plan wearing a diagnosis as a hat, and a reader who wanted the wound found will
say so.

### One spine through all four

Name the threads **A, B, C** — three, occasionally four, never more than five —
and run the same keys, in the same order, under the same words, through every
part:

```html
<!-- 1 problem -->  …traced here through to their fix:
                    <strong>A &middot; single points of failure</strong>, …
<!-- 2 pain   -->  <div class="pain-title">A &middot; Single points of failure</div>
<!-- 3 cause  -->  <div class="pain-title">A &middot; Single points of failure</div>
<!-- 4 fix    -->  <div class="wave-t">A &rarr; Wave 1</div>
```

Two things follow from this and both matter.

**Put parts 2, 3 and 4 in the same column geometry.** Three cards across, in the
same order, in three stacked bands. Column position then carries the key, so the
reader's eye traces A down the page without being told to. A table with a label
column does the same job in more space and less clearly.

**Do not organise the solution by time.** A roadmap section titled
Standardise / Optimise / Automate is phased by calendar and answers a question
nobody asked at that point. Organise it by A, B, C and carry the wave inside
each card. The reader wants to know which wave fixes *their* problem.

`audit_spine.py` enforces all of it.

---

## Step 1 — Read the sources before deciding anything

Read every source end to end first. Three specific things to look for, because
each one changes the page:

- **Contradictions between sources.** Two documents giving a threshold as $150
  and $100, or one calling a control a formal rule and another calling it an
  informal habit. Say so on the page. A named conflict is a finding; a quietly
  picked side is a defect.
- **What the corpus does not carry.** If there are no volumes, handling times or
  cycle times anywhere, then no saving can be honestly asserted, and the page
  must say that rather than reach for a benchmark.
- **The undocumented layer.** Recurring exceptions, account nuances, unofficial
  workarounds, rework drivers. This is usually the most valuable material in the
  pile and it is usually in the least formal document.

Then pick the spine. Three findings that between them account for every item in
the sources, not three findings that sound good.

## Step 2 — Write the parts

- **Specifics, not categories.** "Manual handling" is a category. "Double
  processing is prevented by colouring mailbox items orange and green by hand"
  is a finding. Every card wants a lead sentence and three to five concrete
  facts under it. A bullet list packs specifics into a narrow column far better
  than prose and an executive scans it faster.
- **Quote the source when the source is damning.** If the entire guidance on
  open items is "keep a close eye on all the RAs", print those words.
- **Name what each fix closes.** End each solution card with the source item ids
  it retires. It makes the solution auditable and proves the page read the whole
  corpus:
  `Closes G-03 G-06 G-08 · retires WA-05 WA-09 WA-10`
- **Roles, not names, on the printed sheet.** Individuals can go in the screen
  layer. A printed page naming four people gets forwarded further than you think.
- **No meta-commentary.** "What changed", "as requested", "note the revision"
  belong in the covering message.

## Step 3 — Mark provenance on the page itself

Three markers, and the distinction between the last two is the point:

| Marker | Means |
|---|---|
| `<span class="src">D1 D3</span>` | these documents state it |
| `<span class="src calc">D1 counted</span>` | our arithmetic over a source's table — the source does not state this figure |
| `<span class="src ours">ours</span>` | our recommendation; no source asks for it |

Marking a derived figure as if the source stated it is the failure this prevents.
"Eleven of the nineteen decision points" was tagged `D1` when D1 never contains
the number nineteen — it lists the points and we counted them. One word of
difference, and it is the difference between a citation and a fabrication.

Close with a `.source-box` naming every document, and stating what the corpus
did **not** contain. An undeclared gap is the one defect a reader cannot detect
for themselves.

## Step 4 — Prove it

Five scripts. Run all of them; they check different failures.

| Script | Question |
|---|---|
| `audit_spine.py` | do the four parts carry the same keys, in order, under the same labels? |
| `audit_source_coverage.py` | is every item the sources raise accounted for on the page? |
| `audit_page_tokens.py` | is every number, code and date on the page in a source, or marked as derived? |
| `audit_vocabulary.py` | is any *word or phrase* on the page foreign to the corpus? |
| `fit_one_page.py` | how many mm over one page is it? |
| `measure_blocks.py` | which blocks are eating the page? |

`audit_vocabulary.py` is the one to run when the brief is "only from these
documents". Tokens catch invented numbers; vocabulary catches invented subject
matter, which is the failure that survives a proofread. It hands back a short
residual for a human to read — connective language is expected, a term the corpus
never uses is not. On a page whose sources all said "Phase 1", it was what
surfaced that the deliverable had been saying "Wave 1" throughout, in a document
that linked to a roadmap saying "Phase".

Plus `check_report.py` and `check_print.py` from `ibm-carbon-report`.

`audit_source_coverage.py` takes a small JSON config per source — the selector
that finds its items and a pattern per item saying what would count as covering
it. Writing those patterns is the work; be specific, because a shared generic
word is not coverage.

### Audits lie, and they lie in your favour

Every one of these was a real false pass on a real deliverable. Check the tool
before you trust the tool:

- **A regex that strips the screen layer ate the page body.** A pattern matching
  the nav's nested `</div>`s ran past its own closing tag and swallowed
  everything after it, so every item reported as absent from the print. Strip
  markup with a parser, never a regex.
- **A case-insensitive acronym matched inside a word.** `OAR` under `re.I`
  matches `dashboard`, which passed an item the page never mentioned. Anchor
  short uppercase tokens with `\b` and check the case.
- **A shell heredoc ate one level of backslash** and wrote a literal backspace
  character into the regex, so the pattern silently never matched. Write scripts
  with a file tool, not a heredoc, and grep your own scripts for control
  characters when a pattern mysteriously fails.
- **Coverage counted the solution as diagnosis.** A pain point named in "how it
  gets fixed" is a fix, not a finding. Counting it reported 8 of 9 covered when
  the truth was 6 of 9. Cut the page at the solution heading before testing.
- **Tooltip text in an attribute escapes every audit.** `title="..."` and
  `data-tip="..."` are invisible to text extraction, so a fabricated claim
  in a tooltip would sail through. Put bubble text in real child elements.
- **`len(str)` is characters, not bytes.** A builder that prints
  `wrote X (%d bytes)` from `len(page)` under-reports by every multi-byte
  character and CRLF, and the mismatch against `ls` reads as
  nondeterminism between builds. Ten minutes were spent chasing that
  phantom. Print `len(page.encode('utf-8'))`.
- **A stale PDF passed.** Delete the target before rendering and compare its
  mtime to the run's start.
- **A hand-written claim list kept passing a page it no longer described.** 35
  claims, all 35 confirmed against the sources, green every time — and 17 of them
  had been edited off the page two rewrites earlier. The check was true and
  irrelevant, which is the hardest kind of wrong to notice. Any curated list must
  be pinned to the artifact: check each entry is still *on the page* before
  checking it against the sources, and fail if it is not. Better, prefer the
  audits that need no list.

When a check passes first time on something you have not verified by hand, that
is a reason to look at the check.

## Step 5 — Make it fit

`fit_one_page.py` gives the gap in millimetres. Then, in this order:

1. **`measure_blocks.py` at the true print width.** Set the viewport to the
   printed content width — sheet minus both margins, 188mm for A4 at 11mm. A
   block measured in a 1280px window is far shorter than the same block in a
   188mm column. Measuring at the browser default reported a 193mm page for a
   document that genuinely needed 296mm, and every conclusion drawn from those
   numbers was wrong.
2. **Layout before wording.** Three stacked cards became three across and
   recovered 69mm where word-trimming had barely moved the needle. An
   equal-width flex row is as tall as its fullest column: widening that one
   column by a third shortened three bands at once, for nothing. Headings are
   usually oversized in print — three `h2` at the kit default were 32mm of a
   210mm sheet.
3. **Wording last, and cut connective tissue, not facts.** If a fact has to go,
   say which one and why, rather than shipping a thinner page quietly.
4. **Leave 5mm.** A sheet with 1mm to spare is one font substitution away from
   being two pages on someone else's machine.

Scope page-level compaction to `@media screen`. Unscoped absolute sizes ride
over the kit's smaller print base and inflate the sheet — a one-pager silently
became two this way, and every word trimmed to fix it was wasted until the CSS
was scoped.

## The interactive layer

Three interactions have earned their place on this kind of page, all from the
kit, all screen-only so the sheet never changes:

- **Hover annotations** (`.tip` > `.tipbox`): the detail behind a figure. Six to
  eight on the printed prose is the right count; annotate the figures a reader
  would question, not every number. Two hard rules. The bubble text is **lifted
  from the sources and carries a `src` marker inside the bubble** — an
  annotation is a claim like any other. And it lives in a **real element, never
  a `title=`/`data-` attribute**, so the token and vocabulary audits read it;
  attribute text escapes them, and unaudited text is exactly what the page must
  not carry.
- **Phase line** (`.phaseline`): time is the one axis the solution cards cannot
  show. Widths are the phases' real durations — never equal thirds for a
  3-6-9 arc. Keep it off the A/B/C colours: the spine is identity, this is time.
- **An animated variant**, when someone asks for more motion: KPI strip with the
  kit's count-up, an SVG month-ruler with gate markers (zoom and pan come free
  from `.svgwrap`), readiness bars. Emit it from the **same builder as a second
  output file** — same BODY, extras inserted by anchored string replacement —
  so the two variants cannot drift. Both must pass the same print check: the
  extras are screen-only, and the two files print the same sheet.

## The screen layer earns its keep

Print drops `.screen-only`, so the interactive version can carry what will not
fit: the full evidence behind each finding, the complete register of source
items, the named individuals, a zoomable diagram, the conflicts between sources.
The sheet that reaches the room stays one sheet. Say in the covering note that
the HTML holds more than the PDF, or nobody opens it.

---

## Deliverables

| File | What |
|---|---|
| `<Name>_One-Pager.html` | the artifact — self-contained, forwardable, prints to one page |
| `<Name>_One-Pager.pdf` | the same, rendered |
| `build_<name>.py` | the builder. Never hand-edit the HTML; edit the builder and rebuild, or the next change loses the last one |
| `audit_*.py` + `*.json` | the proofs, kept beside the deliverable so the next person can re-run them |

Lift text from a source with a parser rather than retyping it. A generated
fragment cannot drift from its source; retyped prose drifts on the first edit.

---

## Reference

`reference/worked-example.md` — the [CLIENT] Canada CA10 Returns & Refusals run:
four source reports to one sheet, the spine that was chosen and why, all seven
checks, and the numbers each fix moved.

> **Note on `qa/`** — the scripts in `qa/` need a real browser (playwright) or
> an HTML parser (bs4) and cannot run inside the Process Studio sandbox, which
> disables a whole skill when a script in `scripts/` names a package its runtime
> lacks. They are author-side proofs, so they live in `qa/` and are run locally:
> `pip install playwright pypdf beautifulsoup4 && playwright install chromium`.
> Everything in `scripts/` runs anywhere.
