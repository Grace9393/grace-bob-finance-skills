"""Seed sample data for the exception-resolution demo (50 exceptions, 3 sources,
with deliberate cross-source duplicates)."""

import json
import random

import pandas as pd

random.seed(11)

PROCESSES = ["OTC", "PTP", "RTR", "FPA"]
TYPES = {
    "OTC": ["UNMATCHED_CASH", "CREDIT_BLOCK", "REBATE_DISPUTE"],
    "PTP": ["BLOCKED_INVOICE", "GRIR_MISMATCH", "DUPLICATE_PAYMENT"],
    "RTR": ["JOURNAL_REJECTED", "IC_BREAK", "RECON_VARIANCE"],
    "FPA": ["FORECAST_GAP", "ALLOC_ERROR"],
}
OWNERS = ["m.santos", "c.ortiz", "p.rao", "c.owens", None]

rows = []
for i in range(1, 41):
    p = random.choice(PROCESSES)
    rows.append({
        "document_no": f"DOC{9000+i}",
        "process_area": p,
        "exception_type": random.choice(TYPES[p]),
        "amount": round(random.uniform(500, 250000), 2),
        "age_days": random.randint(1, 95),
        "owner": random.choice(OWNERS),
        "status": random.choices(["OPEN", "CLOSED"], [0.7, 0.3])[0],
        "description": "Auto-extracted from ERP workflow queue",
    })
erp = pd.DataFrame(rows)
erp.to_csv("sample_data/erp.csv", index=False)

# ServiceNow: 12 tickets, 6 of which duplicate ERP items (same ref+type)
snow_rows = []
dupes = erp.sample(6, random_state=1)
for _, d in dupes.iterrows():
    snow_rows.append({"number": d["document_no"], "u_process_area": d["process_area"],
                      "category": d["exception_type"], "u_amount": d["amount"],
                      "opened_at": "2026-05-20 09:00:00",
                      "assigned_to": {"display_value": d["owner"] or "unassigned"},
                      "state": "OPEN", "short_description": "Ticket raised for ERP break"})
for i in range(6):
    snow_rows.append({"number": f"INC{7000+i}", "u_process_area": random.choice(PROCESSES),
                      "category": "ticket", "u_amount": None,
                      "opened_at": "2026-06-15 14:30:00",
                      "assigned_to": {"display_value": random.choice(OWNERS[:4])},
                      "state": "OPEN", "short_description": "Manual escalation via email"})
json.dump({"records": snow_rows}, open("sample_data/snow.json", "w"), indent=1)

# Tracker: 10 rows, 5 duplicating ERP
tr = []
for _, d in erp.sample(5, random_state=2).iterrows():
    tr.append({"Reference": d["document_no"], "Process": d["process_area"],
               "Issue Type": d["exception_type"], "Amount": d["amount"],
               "Age Days": d["age_days"], "Owner": d["owner"], "Status": "OPEN",
               "Notes": "Tracked in team spreadsheet"})
for i in range(5):
    tr.append({"Reference": f"TRK{500+i}", "Process": random.choice(PROCESSES),
               "Issue Type": "manual", "Amount": round(random.uniform(100, 5000), 2),
               "Age Days": random.randint(5, 40), "Owner": random.choice(OWNERS[:4]),
               "Status": "OPEN", "Notes": "Follow-up owed to market team"})
pd.DataFrame(tr).to_excel("sample_data/tracker.xlsx", index=False)

print("seeded: 40 ERP + 12 ServiceNow (6 dupes) + 10 tracker (5 dupes) = 62 rows, 11 duplicates")
