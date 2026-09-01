---
name: ibm-carbon-report
description: Produce a client-facing HTML deliverable in the IBM Carbon house format — IBM Plex Sans, Carbon v11 blue palette, KPI tiles, finding and recommendation cards, wave roadmaps, maturity bars, sticky section navigation, and nine built-in interactions (scroll reveal, bar fill, KPI count-up, section scroll-spy, collapsible sections, severity filter chips, live table filter, SVG zoom, drag-to-pan) plus CSS-only hover annotation bubbles, a duration-true phase line and a call-to-action button, in a single self-contained file that prints cleanly. Use whenever a report, pitch, roadmap, assessment, analysis page or one-pager needs to look like the IBM deck it sits alongside, when someone asks for "the blue interactive format", "the same style as the other artifacts", "on-brand HTML", or when a working document is being promoted to something a client will see.
metadata:
  argument-hint: "[what the deliverable is, and the source it is built from]"
---

# IBM Carbon report — conduct guide

There are two house formats in circulation, and picking the wrong one wastes a
rewrite.

| | Plain working format | **This kit** |
|---|---|---|
| Audience | the team, an internal reviewer | the client, a steering committee |
| Look | system font, neutral greys | IBM Plex Sans, Carbon blue |
| Behaviour | static | nine interactions, all optional-enhancement |
| Print | incidental | designed for it |
| Cost to produce | minutes | an hour, and worth it once |

Use the plain format for registers, working notes and anything that will be
superseded next week. Use this kit when the artifact carries the engagement's
face. Promoting a working document to this format later is cheap; demoting a
client artifact never happens.

---

## Step 1 — Assemble the file

The kit is three files and they go in one output:

| asset | where it goes |
|---|---|
| `assets/carbon-report.css` | inside `<style>`, verbatim |
| `assets/carbon-report.js` | inside `<script>` at the end of `<body>`, verbatim |
| `assets/skeleton.html` | copy it, delete unused components, fill the rest |

**Do not retype the CSS or the JS.** They are lifted byte-identical from the
artifacts already in circulation, which is the only reason the family looks like
a family. Every hand-rewrite drifts the palette by a few hex values and the
drift compounds across a folder.

Both files end with a marked **print-correctness addendum** — an appended block,
not an edit to the lifted code. Fix bugs there, the same way, so the original
stays diffable against the artifacts it came from.

**One file, no exceptions.** No `<link>`, no CDN, no external images, no linked
SVG. The client opens this behind a firewall, forwards it, prints it to PDF, and
opens it again in six months. Inline everything, including diagrams.

---

## Step 2 — Choose the components

Everything below is in `skeleton.html` with the markup it expects.

| Component | Class | Use it for |
|---|---|---|
| Title block | `.hero` `.eyebrow` | one per page |
| Standfirst | `.summary-box` | the one finding the reader must leave with |
| KPI tiles | `.kpi-strip` `.kpi .num .lbl` | three to six numbers, never seven |
| Section heading | `<h2 id>` | blue, light weight; the id feeds the section nav |
| Panel | `.block` `.block-title` | an aside that stands apart from the run of the page |
| Table | plain `<table>` | solid blue header, hover rows, filter added by the JS |
| Tags | `.tag-red/-amber/-green/-blue/-purple` | severity, status, applicability |
| Finding | `.pain-card` `.pain-title`, add `.critical` | what is wrong |
| Recommendation | `.enh-card` `.enh-title` `.enh-meta` | what to do about it |
| Legend | `.legend` `.legend-dot` | whenever colour carries meaning |
| Maturity bar | `.bar-bg` > `.bar[data-w]` | `data-w` is fill width in px on a 120px track |
| Wave | `.wave` `.w2` `.w3` `.wave-t` `.wave-m` | phased roadmaps, three phases |
| Diagram | `.svgwrap` > inline `<svg>` | gets zoom chips and drag-pan automatically |
| Hover annotation | `.tip` > `.tipbox`, add `.flip` near the right edge | sourced detail behind a figure or term. The bubble text goes in the element, never in a `title=` attribute — attribute text escapes the provenance audits. Hidden in print. |
| Phase line | `.phaseline` > `.ph.p1/.p2/.p3` with `.ph-t` `.ph-m` | phased arc; set each `.ph`'s flex to the phase's real duration in months so the widths tell the truth. Wrap in `.screen-only` on a one-pager. |
| Call to action | `.btnrow` > `.btn`, add `.secondary` | a link to a companion document. Hidden in print by default — a button on paper is an instruction the reader cannot follow. Link by relative path so the pair survives being saved elsewhere. |
| Provenance | `.source-box` | what it was built from, and what was missing |
| Navigation | `.topnav` `.nav-row` `.secnav` `.totop` | one `.secnav` link per `<h2 id>` |
| Page break | `.pagebreak` | where a printed section should start fresh |

The KPI count-up only fires on a `.num` whose text begins with a number, so
`219` and `71%` animate and `Real-time` sits still. That is intended — do not
force a number into a tile that does not have one.

**Three behaviours appear on their own, driven by what is on the page:**

| Trigger | What the script adds |
|---|---|
| More than three `.pain-card` **in one container** | a severity filter bar — All / High / Medium / Low chips and an "n of N shown" count. Give each card `.critical` or `.low`, or leave it plain for the middle band. The bar governs only the container it sits in, so a page may carry a second row of `.pain-card` (root causes under findings, say) without the chips reaching across into it. Three or fewer cards get no bar — a filter over three items is furniture. |
| A `<table>` with **8 or more** body rows | a text filter box above it, with a live match count. Shorter tables get nothing, which is correct. |
| Every `<h2 id>` outside the hero | a click-to-collapse toggle, with a minus marker in the right margin. |

The first two inject a `.ctl` bar into the flow. It is screen furniture — hide it
in print or it lands in the middle of the PDF. The collapse marker is a
`::after` on `h2.collapsible` and needs hiding separately; the kit's print
addendum now does that.

The remaining behaviours need markup you author: `.secnav a` plus `<h2 id>` for
the scroll-spy, `.bar[data-w]` for the fills, and `.svgwrap` around an inline
`<svg>` for zoom and drag-pan. The script has eight blocks for nine behaviours —
zoom and pan share one.

## Screen and print are two jobs

A page can be an artifact people click through and a document that prints to a
fixed number of pages. Those pull in opposite directions, and the way to have
both is to split them rather than compromise:

```css
@media print{
  .screen-only,.topnav,.totop,.ctl,.ctl.on{display:none!important}
}
```

Put the navigation, diagrams and any exploratory detail inside `.screen-only`.
One trap: `.screen-only` is `display:block`, so putting the class **directly on
a flex component** (`.kpi-strip`, `.phaseline`, a `.row3`) overrides its flex
and stacks the children into a column. Wrap the component in a screen-only
`<div>` instead — this stacked a four-tile KPI strip into a tower before it
was caught on a screenshot.
Print then drops the whole interactive layer and the printed page is exactly the
static document you laid out — no negotiation between the two. A one-pager needs
this most: the screen version can carry a zoomable roadmap and a readiness chart,
and the sheet that reaches the room stays one sheet.

**Scope your own layout CSS to `@media screen`.** The kit sets a smaller base for
print. Page-level compaction written unscoped uses absolute sizes, so it rides
straight over those print values and inflates the sheet rather than shrinking it.
A one-pager built this way silently became two pages, and every word trimmed to
fix it was wasted effort until the CSS was scoped.

---

## Step 3 — Write to the house voice

The format is only half the house style; the prose is the other half.

- **No marketing words.** leverage, synergy, best-in-class, seamless,
  world-class, cutting-edge, game-changing, holistic, unlock the power of.
  `check_report.py` fails the page on these.
- **Sentences average 18 words**, hard cap 28. Split the long enumerations.
- **No meta-commentary in the artifact.** "What I changed", "note the revision",
  "as requested" belong in the covering message, not the page.
- **State the urgency.** Rank findings by severity, not by document order.
- **Declare what is missing.** If the source was partial, say so on the page, in
  the `.source-box`, with numbers. An undeclared gap is the one defect a reader
  cannot detect for themselves, which makes it the worst one to leave.
- **Never assert a number the source does not carry.** Volumes, handling times,
  FTE counts and benefit percentages come from client data or they do not appear.

---

## Step 4 — QA before it leaves

```
python scripts/check_report.py OUTPUT.html
```

| Fails the page | Warns |
|---|---|
| any external URL, `<link>`, `<iframe>`, `<object>` | colours outside the Carbon token set |
| IBM Plex not set | `<svg>` with no `aria-label` |
| `IntersectionObserver` with fewer than two failsafe timeouts | `<h2>` with no `id` while a section nav exists |
| no `@media print` block | no statement of what the page was built from |
| | marketing words |

Exit codes: 0 clean, 2 warnings, 1 failure. `--strict` fails on warnings too.

Then look at it: print preview at A4, and the page at 1280px and 375px wide.

**If the page count matters, render it — do not estimate it.**

```
python qa/check_print.py OUTPUT.html --pages 1
```

It prints the file through headless Chrome and counts what comes out, then checks
the two defects that only appear on paper: a KPI tile that rendered as `0`, and a
collapse marker leaking into the PDF.

Estimating height from the markup does not work. An earlier version of that script
counted characters and reported "98%, fits" for a document that printed to two
pages. If you need to know how far over you are, bisect the sheet size — render at
`@page{size:210mm Nmm}` for a few values of N and find the shortest sheet that
still yields one page. That number is the real content height.

When a page is genuinely over, layout beats wording. Moving three stacked cards
into a three-across row recovered 69mm on a sheet that word-trimming had barely
moved.

---

## Why the failsafes matter

Three interactions are driven by `IntersectionObserver`, and each starts by hiding
or zeroing the thing it will later reveal. If the observer never fires — an old
browser, a print job, a headless render, a page opened scrolled to the bottom —
the content stays hidden and the client receives a document with blank rows and
empty bars.

The kit carries failsafe timeouts at 2.5 seconds:

```js
/* failsafe: whatever happens, nothing stays hidden */
/* failsafe: a bar must never be left empty */
```

**The count-up did not have one, and it cost a deliverable.** A finished one-pager
printed with every KPI tile reading `0`, because the numbers animate from zero and
nothing snapped them back. The lesson is not that this bug existed but that the
guide claimed every animation was covered when one was not — the claim was never
checked against a real print.

`assets/carbon-report.js` now ends with a print-correctness addendum that captures
the authored numbers before anything animates, then restores them, fills the bars,
reveals hidden blocks and expands collapsed sections on `beforeprint`, on a print
media-query change, and once on a timer for renderers that fire neither. Both asset
files carry that addendum as an appended, marked block; the lifted original above
it is untouched.

If you add a ninth interaction that hides or zeroes something, extend `settle()`.

---

## What this kit is not

- **Not a slide deck.** For `.pptx` use `ibm-branded-pptx`.
- **Not the real Carbon component library.** This is the token set and a hand-built
  component vocabulary, not `carbon-components`. A page that needs genuine Carbon
  widgets — data tables with sorting, toggles, tiles — is a different build, and
  one such dashboard already exists in the [CLIENT] folder as the precedent.
- **Not dark-mode aware, deliberately.** These are printed and PDF'd. A dark variant
  would fork the palette for an audience that does not exist. Do not add
  `prefers-color-scheme` to `carbon-report.css`.

> **Note on `qa/`** — the scripts in `qa/` need a real browser (playwright) or
> an HTML parser (bs4) and cannot run inside the Process Studio sandbox, which
> disables a whole skill when a script in `scripts/` names a package its runtime
> lacks. They are author-side proofs, so they live in `qa/` and are run locally:
> `pip install playwright pypdf beautifulsoup4 && playwright install chromium`.
> Everything in `scripts/` runs anywhere.
