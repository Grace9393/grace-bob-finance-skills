"""Seed raw quarter-pack documents with planted sensitive data (accounts, IBANs,
emails, names) so the sanitizer's redaction counts are verifiable."""

import pathlib

RAW = pathlib.Path("raw")
RAW.mkdir(exist_ok=True)

RAW.joinpath("q2_close_report.txt").write_text("""Q2 2026 Close Report — CONFIDENTIAL
Prepared by: Elena Marchetti
Contact: elena.marchetti@client.example.com / +41 44 555 12 34

Close calendar: entities E200 and E300 missed WD3 (journal backlog in account 40-123456).
Journal rejections doubled vs Q1, concentrated in intercompany account 41-778899.
Settlement account IBAN CH9300762011623852957 saw unreconciled inflows of 2.1m.
The close delay pushed two billing runs into July, deferring ~3.4m of Q2 revenue.
""", encoding="utf-8")

RAW.joinpath("ar_aging.csv").write_text("""bucket,region,amount_m,note
0-30,NA,42.1,normal
31-60,EMEA,18.7,slipping
60+,EMEA,25.3,concentrated in 8 accounts incl 55-441199; escalation owner maria.silva@client.example.com
60+,APAC,6.2,stable
""", encoding="utf-8")

RAW.joinpath("cash_report.txt").write_text("""Q2 2026 Cash Performance — CONFIDENTIAL
Prepared by: Tomas Berg

DSO rose 6 days in Q2, driven by EMEA overdue receivables past 60 days (25.3m, +9.1m QoQ).
Early-payment discounts taken by customers cost 1.8m against 0.9m of financing benefit.
Treasury account IBAN DE89370400440532013000 held idle balances averaging 14m.
Recommended focus: collections surge on the 8 concentrated EMEA accounts, renegotiate
discount terms, and sweep idle balances weekly. Contact: tomas.berg@client.example.com
""", encoding="utf-8")

print("seeded 3 raw documents in raw/ with planted PII (names, emails, IBANs, account numbers, phone)")
