# Worked example — Nestlé Canada CA10 Returns & Refusals

Four analysis reports to one A4 sheet, August 2026. Every number below is from
the actual run, including the things that went wrong, because those are the part
worth reading twice.

## The inputs

| Code | Document | What it carried |
|---|---|---|
| D1 | Business rules, decision logic and controls | 19 classified decision points, thresholds, validation rules |
| D2 | Complete rules and tribal knowledge | 10 gaps (G-01…G-10), 10 workarounds (WA-01…WA-10) |
| D3 | Full process analysis, tools, roadmap | 9 pain points (P1…P9) |
| D4 | Transformation roadmap — standardise, optimise, automate | the three waves |

The four together carried **no volumetrics at all** — no volumes, handling
times, FTE counts, exception rates or cycle times. That single fact decided the
tone of the page: no saving could be honestly claimed, and the `.source-box` says
so. Wave 1's first job became "set the baseline", which is a stronger
recommendation than an invented percentage would have been.

## The spine

Three findings, chosen so that every one of D3's nine pain points and D2's
twenty items lands on exactly one of them:

| Key | Finding | Carries |
|---|---|---|
| **A** | Single points of failure | 6 of D2's 20 |
| **B** | Fragmented, manual handling | 7 of D2's 20 |
| **C** | Nothing is measured | 7 of D2's 20 |

Parts 2, 3 and 4 are three bands of three cards in the same column order, so A
sits directly above A. Part 4 names what it closes:
`Closes G-03 G-06 G-08 · retires WA-05 WA-09 WA-10`.

## What the checks caught

| Check | Result | What it found on the way |
|---|---|---|
| `audit_spine.py` | 4 parts, one 3-item spine | the problem statement wrote `A single points of failure` without the separator, so it carried no key at all |
| `audit_source_coverage.py` (D3) | 9 / 9 | 3 pain points were absent — P3, P5, P7. P7 had been lost when the root-cause table went from 5 rows to 3 |
| `audit_source_coverage.py` (D2) | 20 / 20 | — |
| `audit_page_tokens.py` | 22 / 22 traced | "eleven of nineteen" was tagged `D1`, but D1 never contains the number nineteen — we counted its table. Became `D1 counted` |
| `fit_one_page.py` | 289 mm of 297 | — |
| `check_report.py` | PASS | — |
| `check_print.py` | 1 page | KPI tiles printed as `0`; a stray collapse marker printed |

## The three audits that lied

Each of these passed while being wrong. They are in the guide's trap list
because none of them is detectable by reading the output.

1. **Coverage counted the solution as diagnosis.** Reported 8 of 9 when the
   truth was 6 of 9: "duplicate checks move into SAP scripting" is a fix, and it
   was being read as evidence that duplicate detection had been diagnosed.
   Fixed by cutting the page at `h2#fix` before testing.
2. **A regex ate the page body.** The pattern stripping the nav ran past its own
   closing tag, so all twenty D2 items reported as absent from the print. A
   false negative that looks exactly like a real one — and the temptation is to
   go and "fix" the page.
3. **`OAR` under `re.I` matched inside `dashboard`.** An item the page never
   mentioned passed. Anchored to `\bOAR\b`.

A fourth was not an audit but a tool: a shell heredoc ate one level of backslash
and wrote a literal backspace character into a regex, which then silently never
matched. Scripts get written with a file tool, not a heredoc.

## Fitting the page

Started 33 mm over after the spine was added, then 19 mm over after the D2
specifics went in. The order that worked:

| Move | Recovered |
|---|---|
| three stacked cards → three across | 69 mm (earlier round) |
| print `h2` from the kit default to 13.5px | 14 mm — three headings were 32 mm of a 210 mm sheet |
| middle column of every band widened to 1.42× | ~19 mm, no words lost |
| print base 10.5px → 9.6px, leading 1.30 | ~16 mm |
| trailing margin under `.source-box` | 6 mm for nothing |
| prose trimming, all rounds combined | ~8 mm |

**Layout returned about ten times what wording did.** The first instinct — cut
sentences — was the least effective lever available, and two rounds of it were
spent before anything was measured.

One measurement was itself wrong: block heights taken in the browser's default
1280 px viewport reported a 193 mm page for a document that genuinely needed
296 mm. The columns reflow. `measure_blocks.py` now defaults to 188 mm.

## What shipped

```
Pitch_CA10-RR_Executive-One-Pager.html   one sheet, screen layer holds the rest
Pitch_CA10-RR_Executive-One-Pager.pdf
build_exec_onepager.py                   the builder; the HTML is never hand-edited
build_d2_register.py                     lifts D2's twenty items into a fragment
d2_register_fragment.html                generated, not hand-written
coverage-D3-painpoints.json              audit configs, kept beside the deliverable
coverage-D2-gaps-workarounds.json
```

An animated variant was later emitted from the same builder as a second file
(`…_Animated.html`): KPI count-up strip, an SVG eighteen-month ruler with the
two D4 gates, readiness bars 11/3/4/1 — all screen-only, so both variants print
the identical 969-word sheet, and the audits run against the animated superset.

The screen layer carries what would not fit: the evidence behind each finding,
the full twenty-item register with D2's own risk ratings, the four named
individuals, and one conflict between sources that still needs settling with the
client — D1 carries the OAR attachment check as formal rule RULE-VAL-03, D2
records it as an informal habit new processors are never taught.
