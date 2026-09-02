# ibm-carbon-report - author-side QA

`check_print.py` renders the report to PDF and inspects the result, to verify the
page still prints cleanly (page count, no clipped blocks, footers intact).

It drives a real browser, so it cannot run inside the Process Studio sandbox and
lives here rather than under `skills/`. Everything the skill itself needs is in
`skills/ibm-carbon-report/scripts/`, which is standard library only.

Run locally:

    pip install -r requirements.txt
    playwright install chromium
    python check_print.py OUTPUT.html --pages 1
