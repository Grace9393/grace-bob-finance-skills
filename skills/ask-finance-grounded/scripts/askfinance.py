"""Client-specific Ask Finance — Proposal 5 (Tui).

Governance-first pipeline: sanitize -> upload to a tenant-isolated ICA document
collection -> grounded (cite-or-refuse) queries -> golden-question eval harness.

Usage:
    python askfinance.py sanitize  --in raw/ --out clean/
    python askfinance.py upload    --dir clean/ --name q2-close-cfo
    python askfinance.py ask       --collection <id> --q "Top 3 cash levers this quarter?"
    python askfinance.py eval      --collection <id>

Env: ICA_API_KEY, ASKFIN_AGENT (assistant id).
"""

import argparse
import json
import os
import pathlib
import re

import requests

ICA_HOST = "https://servicesessentials.ibm.com"
HEADERS = {"Authorization": f"Bearer {os.environ.get('ICA_API_KEY', '')}"}

JUNK = {"desktop.ini", "thumbs.db", ".ds_store"}


def corpus_files(dir_path: str):
    return [f for f in sorted(pathlib.Path(dir_path).glob("*"))
            if f.is_file() and f.name.lower() not in JUNK and not f.name.startswith(".")]


SYSTEM_RULES = (
    "Answer ONLY from the attached collection. Every claim must cite the source document "
    "and the specific figure. If the data does not support an answer, state exactly what "
    "data is missing and stop — generic financial advice is a failure, not a fallback."
)

# Challenge-window scrubber. Production path: the client's DLP tool instead.
SCRUB_PATTERNS = [
    (re.compile(r"\b\d{2,3}-\d{6,}\b"), "[ACCT]"),                        # account numbers
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"), "[IBAN]"),          # IBANs
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[EMAIL]"),              # emails
    (re.compile(r"\b(?:\+?\d[\s-]?){9,14}\d\b"), "[PHONE]"),              # phone-ish
    (re.compile(r"(?i)(prepared by|approved by|contact)[:\s]+[A-Z][a-z]+ [A-Z][a-z]+"),
     r"\1: [NAME]"),                                                       # names in bylines
]


def sanitize_dir(in_dir: str, out_dir: str) -> None:
    outp = pathlib.Path(out_dir); outp.mkdir(parents=True, exist_ok=True)
    hits_total = 0
    for f in pathlib.Path(in_dir).glob("*"):
        if f.suffix.lower() not in (".txt", ".csv", ".md"):
            print(f"SKIP {f.name} (sanitize PDFs/XLSX by exporting to text first)")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        hits = 0
        for pat, repl in SCRUB_PATTERNS:
            text, n = pat.subn(repl, text)
            hits += n
        (outp / f.name).write_text(text, encoding="utf-8")
        hits_total += hits
        print(f"{f.name}: {hits} redactions")
    print(f"sanitized -> {out_dir} ({hits_total} total redactions). Spot-check before upload.")


def upload(dir_path: str, name: str) -> None:
    """Create the tenant-isolated collection. Confirm multipart contract at
    /apis/v3/document_collections in the live Swagger before demo day.
    No API key? Upload the clean/ folder through the ICA UI instead — equivalent."""
    if not os.environ.get("ICA_API_KEY"):
        raise SystemExit(f"ICA_API_KEY not set — upload {dir_path}/ via the ICA UI "
                         f"(collection name: {name}), or use `pack` for the no-collection path.")
    files = [("files", (f.name, f.read_bytes())) for f in corpus_files(dir_path)]
    r = requests.post(f"{ICA_HOST}/apis/v3/document_collections", headers=HEADERS,
                      data={"name": name}, files=files, timeout=300)
    r.raise_for_status()
    print("collection created:", r.json())


def ask(collection_id: str, question: str) -> str:
    if not os.environ.get("ICA_API_KEY"):
        raise SystemExit("ICA_API_KEY not set. Tier A path: `python askfinance.py pack "
                         "--dir clean --q \"<question>\"` builds a paste-ready grounded "
                         "prompt for Bob or an ICA assistant in the UI.")
    r = requests.post(f"{ICA_HOST}/apis/v3/executePrompt", headers=HEADERS, timeout=120,
                      json={"assistantId": os.environ["ASKFIN_AGENT"],
                            "collectionId": collection_id,
                            "systemPrompt": SYSTEM_RULES,
                            "prompt": question})
    r.raise_for_status()
    out = r.json()
    return str(out.get("response", out))


def pack(dir_path: str, question: str, out_file: str = "grounded_prompt.txt") -> None:
    """Tier A (no API, no collection): bundle the sanitized corpus + cite-or-refuse rules
    + question into one paste-ready prompt for Bob or any ICA assistant. Same contract
    as the collection-grounded call; the corpus just rides inline."""
    docs = []
    for f in corpus_files(dir_path):
        docs.append(f"===== DOCUMENT: {f.name} =====\n{f.read_text(encoding='utf-8', errors='replace')}")
    body = (SYSTEM_RULES + "\n\nTHE COLLECTION (sanitized; the only permitted sources):\n\n"
            + "\n\n".join(docs) + f"\n\nQUESTION: {question}\n")
    pathlib.Path(out_file).write_text(body, encoding="utf-8")
    print(f"wrote {out_file} ({len(docs)} documents inlined) — paste into Bob / ICA assistant.")


# Golden questions: (question, fragments a grounded answer MUST contain, refusal_expected)
GOLDEN = [
    ("What drove the DSO increase in Q2?", ["60", "EMEA"], False),
    ("What are the top 3 cash levers this quarter?", ["collection", "terms"], False),
    ("Which entities missed the close calendar and why?", ["close"], False),
    ("What will revenue be in five years?", [], True),   # must refuse: not in the data
]


def run_eval(collection_id: str, canned_file: str = "") -> float:
    """Grounding gate. With --canned answers.json ({question: answer}), scores offline —
    use it to gate manually-collected UI answers when no API key is available."""
    canned = json.load(open(canned_file, encoding="utf-8")) if canned_file else None
    passed = 0
    for q, must, refusal_expected in GOLDEN:
        a = (canned[q] if canned else ask(collection_id, q)).lower()
        refused = any(s in a for s in ("does not support", "data is missing", "cannot answer"))
        ok = refused if refusal_expected else (all(m.lower() in a for m in must) and not refused)
        passed += ok
        print(("PASS " if ok else "FAIL "), q)
    score = passed / len(GOLDEN)
    print(f"\ngrounding score: {score:.0%}  (gate: >= 80% before anyone demos)")
    return score


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sanitize"); s.add_argument("--in", dest="in_dir", required=True); s.add_argument("--out", required=True)
    u = sub.add_parser("upload"); u.add_argument("--dir", required=True); u.add_argument("--name", required=True)
    q = sub.add_parser("ask"); q.add_argument("--collection", required=True); q.add_argument("--q", required=True)
    p = sub.add_parser("pack"); p.add_argument("--dir", required=True); p.add_argument("--q", required=True); p.add_argument("--out", default="grounded_prompt.txt")
    e = sub.add_parser("eval"); e.add_argument("--collection", default=""); e.add_argument("--canned", default="")
    a = ap.parse_args()
    if a.cmd == "sanitize": sanitize_dir(a.in_dir, a.out)
    elif a.cmd == "upload": upload(a.dir, a.name)
    elif a.cmd == "ask": print(ask(a.collection, a.q))
    elif a.cmd == "pack": pack(a.dir, a.q, a.out)
    elif a.cmd == "eval": run_eval(a.collection, a.canned)
