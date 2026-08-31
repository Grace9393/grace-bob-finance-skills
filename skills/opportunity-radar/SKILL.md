---
name: opportunity-radar
description: Build or refresh a competition, hackathon and partner-community radar — sweep 獎金獵人 (bhuntr), Devpost, government programmes and county/city announcements for what is currently open, gate every entry on eligibility (many Taiwanese competitions are students-only), consolidate an existing CRM or 潛在合作名單 into the same schema, and emit a bilingual (中文／English) Excel tracker with deadlines, countdowns and status colour codes. Use when the user asks what competitions or hackathons are open now, asks to find or track 黑客松／競賽／徵件中 opportunities, wants a list of Taiwan communities, organizations, KOLs or 自媒體 to partner with, asks to classify opportunities into 企業／個人／政府, wants an existing partner list or CRM merged into a tracker, or asks for a competition list in both Chinese and English.
---

# Opportunity radar — conduct guide

You are building a decision tool, not a list. The user will act on it: draft an
entry, email a contact, put a date in a calendar. Three rules follow from that.

1. **Eligibility is the gate, not a footnote.** A large share of Taiwanese
   competitions are students-only. Listing one for a company or a working
   professional without flagging that wastes their afternoon. Check 身分限制
   before you write a single admiring sentence about a competition.
2. **Never invent precision.** A deadline you estimated must say it was estimated.
   An invented date is worse than an admitted gap, because nobody re-checks a cell
   that looks exact.
3. **Look on disk before you search the web.** The partner list, the CRM, the
   evidence of who has already been contacted — it is usually already in the
   user's folder under a name nobody remembers.

## Step 0 — Establish the verification date and the actor

Fix today's date; every countdown in the output is measured from it and stamped in
the workbook. Then establish **who is entering**: a company, an individual
professional, a student team, a school. This single fact decides which half of the
findings are actionable, so ask if it is not obvious from context.

## Step 1 — Mine what already exists

Before searching, scan the user's folder for an existing pipeline:

```
python scripts/scan_excel_keywords.py "<folder>" -k CRM 合作對象 自媒體 潛在合作 KOL 社群
```

Sheet-name matches outrank stray cell matches; the script separates them. Read any
list you find **in full**, including the columns that look like clutter — follower
counts, "對方已追蹤我們 IG", owner initials, half-finished notes. That texture is
the difference between a directory and a working CRM, and it must survive into the
output verbatim.

Distinguish carefully between *the user's own* partner list and a client's or a
third party's CRM that happens to sit in the same folder. They are not the same
pipeline and must not be merged.

## Step 2 — Sweep the sources

Read `references/bhuntr-sweep.md` first — it will save you a wasted pass. The
essentials:

- **bhuntr is JS-rendered.** `WebFetch` returns only the page title, which reads
  like an empty result rather than a failure. Use a browser tool.
- **Category `116,117,118` (商業) is where technology, AI, data, startup and
  government-innovation competitions live.** The default listing is dominated by
  art and writing contests; sweeping only that is how you miss 90% of the field.
- **`?page=2` alone redirects to the home page.** Combine:
  `?category=116,117,118&page=2`.
- **Do not click the cookie banner** — it offers only "accept", and every filter is
  reachable by URL anyway.

Then work `references/source-registry.md`: government programmes, county and city
announcements (these never aggregate well — check them individually), corporate
hosts, and communities. For international coverage, Devpost renders for WebFetch;
prefer events that can be entered fully online.

Search in the user's language as well as English. Chinese-language searches surface
university 育成中心 pages that republish competitions with the registration window
spelled out, which is often the only readable source when the organiser's own site
is a JS shell.

## Step 3 — Open the detail page for anything you will recommend

Listing pages give only `還有 27 天`. Detail pages give:

- the exact window — `徵件期間 2026-07-14 15:00 至 2026-08-31 17:00`
- **身分限制 / 國籍限制** — the eligibility gate
- prize structure, team size, contact窗口

Sidebar blocks (「大家都在看」/「小酒館也推薦」) list *other* competitions with exact
timestamps — two or three detail-page visits will hand you a dozen precise dates.
Harvest them deliberately rather than opening every page.

## Step 4 — Classify

Assign each record one of four categories, by **who leads it**, not who funds it:

| | |
|---|---|
| **企業 Corporate** | A company, foundation, association or its ecosystem |
| **個人 Individual** | Individual creators, volunteer communities, student teams |
| **政府 Government** | Central or local government hosts, supervises or funds it |
| **學研 Academic** | A university or academic body hosts it |

And one status: `urgent` (closes within 30 days) · `open` · `soon` · `tbd`
(next edition unannounced) · `closed` · `rolling`.

Keep closed and unannounced entries. A competition that closed last month is next
year's calendar entry, and the note "registration opened in Q2, prepare a proposal
by March" is worth more than a deleted row.

## Step 5 — Build the workbook

Assemble a JSON dataset (schema: `assets/opportunities.example.json`, a real
50-competition / 46-organisation worked example) and run:

```
python scripts/build_tracker.py opportunities.json -o tracker.xlsx
```

Eight sheets: a bilingual overview, 徵件中 Open Now (ZH + EN), the organisation
directory with CRM columns (ZH + EN), the full directory including closed entries
(ZH + EN), and an optional verbatim copy of the source list for traceability.

The script enforces what makes the file trustworthy, so do not hand-build these:

- Chinese and English sheets are generated from **one** record each and cannot
  drift; row N is row N in both.
- Countdowns run from `meta.verified_date`, never the machine clock, so a stale
  file cannot relabel itself as current.
- Records sort by status then deadline; undated records sort last rather than being
  assigned a fabricated date.

When consolidating an existing partner list, promote its columns into the schema
(`legacy_type`, `has_contact`, `contact_zh`, `status`, `owner`) rather than
appending it as a separate block, and tag those rows via `meta.legacy_source_tag`
so the builder tints column A — the user can then see at a glance which contacts
are already warm.

## Step 6 — Report the shortlist, not the spreadsheet

Lead with what closes soonest and what the user can actually enter. For each of the
top few: deadline, prize, **eligibility verdict**, and the specific reason it fits
their work. Then the traps — the well-known competition that turns out to be
students-only, the one whose registration already closed, the entry you had to
correct.

State plainly what you could not verify and why ("the site is JS-rendered and the
deadline is in an image; phone the organiser"). Say which fields are estimates.

If you have swept only part of a source, say so and say what is left. "I searched
the individual competition pages but never opened the listing index" is the kind of
gap that quietly hollows out a deliverable.

## Refreshing an existing tracker

Update `meta.verified_date`, re-check every `urgent` and `open` record against its
source, move newly-passed deadlines to `closed` with a note about next year's
window, and sweep for new entries. Re-run the builder — the countdowns recompute
from the new verification date.

## Publishing

If the user keeps the file in a synced Drive folder, copying it there is the whole
job — the sync client handles the upload. Note that the Drive API cannot overwrite
an existing file in place: uploading mints a new ID and a new link. To keep an
already-shared link alive, the user must use Drive's 「管理版本」/ Manage versions on
the original. Say so rather than silently creating a duplicate.
