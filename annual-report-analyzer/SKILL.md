---
name: annual-report-analyzer
description: Locate, read, and summarize a company's official annual report or 10-K into a cited, executive-ready financial digest. Use this skill whenever the user asks to "search and read" an annual report, 10-K, full-year results, earnings, or FY financials for any company (e.g. "read IBM's 2025 annual report", "summarize Microsoft's latest 10-K", "find TSMC full-year results"), or asks how a company performed in a given fiscal year — even if they don't say "annual report". Also use it as step one when the end goal is a deck, Excel extract, or comparison built from an annual report.
---

# Annual Report Analyzer

Find a company's official annual report for a given fiscal year, read the primary source, and produce a structured, citation-backed summary. Works for any public company.

## Workflow

### Step 1 — Search for the primary source

Run one web search: `<company> <FY year> annual report full year results`.

Rank candidate sources in this order (highest trust first):

1. **Official annual report PDF** hosted on the company's own domain (e.g. `ibm.com/downloads/...`) or investor-relations site
2. **10-K / 20-F filing** on sec.gov (Exhibit 13 often *is* the annual report)
3. **Company newsroom press release** for Q4/full-year results (good for guidance quotes)
4. Reputable financial news (Reuters, Yahoo Finance) — use only to corroborate, never as the primary source

### Step 2 — Apply the fiscal-year trap filter (critical)

Documents dated in year N frequently report fiscal year **N−1** results (full-year results are announced in January–February of the following year). Never trust a filing's date or a search result label alone. Verify the report explicitly covers "the year ended December 31, <target year>" (or the company's actual FY-end) and check the 10-K filing date — the FY-N 10-K is filed in early year N+1. Discard candidates that fail this check.

### Step 3 — Fetch and read

Fetch the best source with PDF text extraction enabled and a generous token limit (~30K). Prioritize reading, in order: Management Discussion Snapshot (or equivalent highlights table), segment results, geographic revenue, cash flow / free cash flow, balance sheet highlights, and the outlook / "Looking Forward" section. One good fetch of the official report usually suffices; fetch the press release additionally only if guidance or CEO quotes are missing.

### Step 4 — Synthesize with citations

Write the digest in your own words. Every specific figure must be traceable to the source (use inline citations if the environment supports them; otherwise state the document and page/section). Paraphrase — never reproduce long verbatim passages.

Cover, in this structure:

1. **Headline results** — revenue, growth (reported and constant currency if given), net income, EPS (GAAP and non-GAAP), margins. Flag one-time items that distort year-over-year comparisons (pension charges, tax benefits, divestiture gains) — do not let a flattering GAAP number pass without context.
2. **Segment breakdown** — revenue, growth, and margin per reportable segment, with the drivers the company names. Call out both the strongest and weakest segment.
3. **Strategy highlights** — major acquisitions/divestitures, R&D themes, announced deals still pending.
4. **Balance sheet and cash** — cash position, debt change, free cash flow, dividends/buybacks.
5. **Outlook** — next-year guidance in the company's own framing.

End with the direct link to the full report and offer concrete next steps (table extraction, branded deck, peer comparison).

## Quality bar

- Numbers must match the primary source exactly — do not average across secondary sources.
- Distinguish GAAP from non-GAAP every time both appear.
- Note recast/reclassified segments (companies change reporting categories; comparisons must be on the same basis).
- If the target-year report does not exist yet, say so and offer the most recent quarter instead — never substitute the prior year silently.

## Hand-offs

After the digest, if the user wants derived artifacts, chain to the appropriate skill rather than improvising:

- Financial tables → Excel: `pdf-to-data`
- Branded slide deck: `ibm-branded-pptx` or `file-to-pptx`
- Web deck: `open-slide-deck`
- Two-report comparison (YoY or peer): `file-comparison`
