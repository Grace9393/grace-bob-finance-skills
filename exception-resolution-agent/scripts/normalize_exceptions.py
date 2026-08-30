"""Exception register builder — Proposal 1 (Finance Exception Resolution Agent).

Merges exceptions from ERP export, ServiceNow export, and Excel trackers into one
deduplicated register, then (optionally) uploads it to an ICA document collection
so the triage agent can cite it.

Usage:
    python normalize_exceptions.py --erp erp.csv --snow snow.json --tracker tracker.xlsx
    python normalize_exceptions.py ... --upload   # also push to ICA collection
"""

import argparse
import json
import os
from datetime import date

import pandas as pd
import requests

ICA_HOST = "https://servicesessentials.ibm.com"   # regional: https://<region>.ica.ibm.com/ica

REGISTER_COLS = ["source", "ref", "process", "type", "amount", "age_days", "owner", "status", "detail"]


def from_erp(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source": "ERP",
        "ref": df["document_no"].astype(str),
        "process": df["process_area"],
        "type": df["exception_type"],
        "amount": pd.to_numeric(df["amount"], errors="coerce"),
        "age_days": pd.to_numeric(df["age_days"], errors="coerce"),
        "owner": df.get("owner"),
        "status": df.get("status", "OPEN"),
        "detail": df.get("description", ""),
    })


def from_servicenow(path: str) -> pd.DataFrame:
    rows = json.load(open(path, encoding="utf-8"))
    rows = rows.get("records", rows) if isinstance(rows, dict) else rows
    df = pd.json_normalize(rows)
    opened = pd.to_datetime(df["opened_at"], errors="coerce")
    return pd.DataFrame({
        "source": "ServiceNow",
        "ref": df["number"].astype(str),
        "process": df.get("u_process_area", "UNMAPPED"),
        "type": df.get("category", "ticket"),
        "amount": pd.to_numeric(df.get("u_amount"), errors="coerce"),
        "age_days": (pd.Timestamp.now() - opened).dt.days,
        "owner": df.get("assigned_to.display_value"),
        "status": df.get("state", "OPEN"),
        "detail": df.get("short_description", ""),
    })


def from_tracker(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return pd.DataFrame({
        "source": "Tracker",
        "ref": df["reference"].astype(str),
        "process": df.get("process", "UNMAPPED"),
        "type": df.get("issue_type", "manual"),
        "amount": pd.to_numeric(df.get("amount"), errors="coerce"),
        "age_days": pd.to_numeric(df.get("age_days"), errors="coerce"),
        "owner": df.get("owner"),
        "status": df.get("status", "OPEN"),
        "detail": df.get("notes", ""),
    })


def build_register(erp=None, snow=None, tracker=None) -> pd.DataFrame:
    frames = []
    if erp: frames.append(from_erp(erp))
    if snow: frames.append(from_servicenow(snow))
    if tracker: frames.append(from_tracker(tracker))
    if not frames:
        raise SystemExit("No sources given.")
    reg = pd.concat(frames, ignore_index=True)[REGISTER_COLS]
    reg["status"] = reg["status"].astype(str).str.upper().replace({"NEW": "OPEN", "1": "OPEN"})
    # same underlying break often appears in ERP *and* a ticket *and* a tracker row
    reg["dupe_key"] = reg["ref"].str.strip().str.upper() + "|" + reg["type"].astype(str).str.upper()
    before = len(reg)
    reg = reg.sort_values("source").drop_duplicates("dupe_key", keep="first").drop(columns="dupe_key")
    print(f"register: {len(reg)} exceptions ({before - len(reg)} cross-source duplicates linked)")
    return reg


def upload_to_ica(csv_path: str, collection_name: str) -> None:
    """Push the register to an ICA document collection (RAG source for the triage agent).
    Confirm the multipart contract at /apis/v3/document_collections in the live Swagger.
    No API key? Skip gracefully — uploading the CSV through the ICA UI is equivalent."""
    if not os.environ.get("ICA_API_KEY"):
        print(f"ICA_API_KEY not set — upload {csv_path} via the ICA UI instead "
              f"(Context/collection: {collection_name}). Pipeline unaffected.")
        return
    headers = {"Authorization": f"Bearer {os.environ['ICA_API_KEY']}"}
    with open(csv_path, "rb") as fh:
        r = requests.post(f"{ICA_HOST}/apis/v3/document_collections",
                          headers=headers,
                          data={"name": collection_name},
                          files={"files": (os.path.basename(csv_path), fh, "text/csv")},
                          timeout=120)
    r.raise_for_status()
    print("uploaded to ICA collection:", collection_name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--erp"); ap.add_argument("--snow"); ap.add_argument("--tracker")
    ap.add_argument("--out", default="exception_register.csv")
    ap.add_argument("--upload", action="store_true")
    a = ap.parse_args()
    reg = build_register(a.erp, a.snow, a.tracker)
    reg.to_csv(a.out, index=False)
    print("wrote", a.out)
    if a.upload:
        upload_to_ica(a.out, f"exception-register-{date.today().isoformat()}")
