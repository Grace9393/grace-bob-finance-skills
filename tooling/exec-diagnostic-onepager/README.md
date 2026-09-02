# exec-diagnostic-onepager - author-side QA

The audit scripts here prove the one-pager holds together: the spine matches
across all four parts, every source item is accounted for, no vocabulary is
foreign to the corpus, and the page still fits on one sheet.

Some parse HTML and some drive a real browser, so they cannot run inside the
Process Studio sandbox and live here rather than under `skills/`. The skill's own
`scripts/audit_page_tokens.py` is standard library only and runs anywhere.

Run locally:

    pip install -r requirements.txt
    playwright install chromium
    python audit_spine.py PAGE.html --lead <id>
