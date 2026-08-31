"""Seed a sanitized-shaped FP&A extract for Hank: 6 months x entities x regions x
products x accounts, long format with scenario column (actual/budget/py)."""

import itertools
import random

import pandas as pd

random.seed(7)

ENTITIES = ["E100", "E200", "E300"]
REGIONS = ["NA", "EMEA", "APAC", "LATAM"]
PRODUCTS = ["Premium", "Core", "Value"]
ACCOUNTS = ["4000_Revenue", "4100_Rebates", "5000_COGS", "6000_Opex", "6100_Marketing"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]

rows = []
for e, r, p, a, m in itertools.product(ENTITIES, REGIONS, PRODUCTS, ACCOUNTS, MONTHS):
    base = {"4000_Revenue": 900000, "4100_Rebates": -60000, "5000_COGS": -420000,
            "6000_Opex": -150000, "6100_Marketing": -70000}[a]
    size = {"NA": 1.4, "EMEA": 1.1, "APAC": 0.8, "LATAM": 0.5}[r] * \
           {"Premium": 1.3, "Core": 1.0, "Value": 0.6}[p]
    budget = base * size * random.uniform(0.97, 1.03)
    drift = random.uniform(0.92, 1.08)
    # engineered story: EMEA Value rebates blow out; APAC Premium revenue misses
    if r == "EMEA" and p == "Value" and a == "4100_Rebates":
        drift = 1.65
    if r == "APAC" and p == "Premium" and a == "4000_Revenue":
        drift = 0.86
    actual = budget * drift
    py = budget * random.uniform(0.90, 0.98)
    for scen, v in (("Actual", actual), ("Budget", budget), ("PY", py)):
        rows.append({"entity": e, "region": r, "product": p, "account": a,
                     "month": m, "scenario": scen, "value": round(v, 2)})

df = pd.DataFrame(rows)
df.to_excel("sample_data/pnl_extract.xlsx", index=False)
print(f"seeded {len(df)} rows -> sample_data/pnl_extract.xlsx")
