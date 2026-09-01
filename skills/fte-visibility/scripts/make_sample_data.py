"""Seed realistic sample data for the FTE model: ~2,400 employees across 24
cost centers, with allocation gaps engineered so unallocated FTE lands near 340."""

import random

import pandas as pd

random.seed(23)

PROCESSES = ["Month-end close", "AP invoice processing", "AR & collections",
             "FP&A reporting", "Master data", "Intercompany", "Treasury ops",
             "Project Phoenix (S/4 migration)", "Project Atlas (shared services)"]

cc_rows, hc_rows, al_rows = [], [], []
emp = 0
for i in range(1, 25):
    cc = f"CC{4000+i}"
    n = random.randint(60, 140)
    cc_rows.append({"cost_center": cc, "cc_name": f"Finance Ops {i:02d}",
                    "actual_cost": n * random.randint(78000, 112000),
                    "owner": random.choice(["m.kowalska", "j.devries", "l.tan", "r.okafor"])})
    # cost centers 19-24 are the "invisible" ones: little or no allocation data
    dark = i >= 19
    for _ in range(n):
        emp += 1
        eid = f"E{emp:05d}"
        fte = random.choice([1.0, 1.0, 1.0, 0.8, 0.6])
        hc_rows.append({"employee_id": eid, "cost_center": cc, "fte": fte})
        if dark and random.random() < 0.75:
            continue  # no allocation rows at all -> fully unallocated
        remaining = 100
        for t in random.sample(PROCESSES, random.randint(1, 3)):
            pct = min(remaining, random.choice([20, 30, 40, 50, 60]))
            al_rows.append({"employee_id": eid, "target": t, "pct": pct})
            remaining -= pct
            if remaining <= 0:
                break
        # note: employees who don't reach 100% are partially unallocated — by design

pd.DataFrame(hc_rows).to_csv("sample_data/hc.csv", index=False)
pd.DataFrame(cc_rows).to_csv("sample_data/cc.csv", index=False)
pd.DataFrame(al_rows).to_csv("sample_data/alloc.csv", index=False)
print(f"seeded {emp} employees, {len(cc_rows)} cost centers, {len(al_rows)} allocation rows")
