#!/usr/bin/env python3
"""
mine_rules.py - deterministic candidate miner for a business rules register.

Reads the markdown produced by deep_extract.py (or any markdown/text corpus) and
pulls out every statement that carries a decision, a threshold, an obligation, an
exception, an approval step, a mapping or a tribal-knowledge marker.

It does NOT decide what a rule means. It narrows a multi-megabyte corpus down to a
few hundred candidate statements with their source location attached, so a model
can classify and normalise them without holding the whole corpus in context.

Usage:
    python mine_rules.py CORPUS.md [CORPUS2.md ...] -o OUTDIR
    python mine_rules.py CORPUS.md --min-len 25 --max-len 400

Outputs, in OUTDIR:
    rule_candidates.csv   one row per deduplicated candidate statement
    rule_candidates.md    the same, grouped by category, for reading
    mining_summary.md     counts by category and by source document

Exit codes: 0 clean, 2 finished with warnings (no candidates in some input), 1 failed.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter, OrderedDict

__version__ = "1.0.0"

# --------------------------------------------------------------------------- #
# Pattern families.
#
# Each family is (name, compiled regex, weight). A statement is a candidate if it
# matches at least one family. Weight only orders the output - a statement that
# carries a literal number is more useful to a designer than one that does not.
# --------------------------------------------------------------------------- #

FAMILIES = [
    (
        "threshold",
        re.compile(
            r"(\$\s?\d[\d,\.]*|\b\d[\d,]*\s?(?:CAD|USD|EUR|PHP)\b"
            r"|\b(?:greater|less|more|lower|higher|equal)\s+than\b"
            r"|\b(?:at least|at most|up to|no more than|maximum|minimum|max|min)\b"
            r"|\b\d+\s?(?:cases|days|hours|characters|digits|%)\b"
            r"|\bexceed(?:s|ing)?\b|\bbelow\b|\babove\b|\bthreshold\b)",
            re.I,
        ),
        3,
    ),
    (
        "conditional",
        re.compile(
            r"\b(?:if|when|in case|once|unless|in the event|should there|"
            r"whenever|provided that|otherwise|in instances|there are times|"
            r"there is a possibility|for some|for those)\b",
            re.I,
        ),
        2,
    ),
    (
        "obligation",
        re.compile(
            r"\b(?:must|shall|cannot|can\'t|is required|are required|not allowed|"
            r"do not|don\'t|never|always|need to|needs to|should not|shouldn\'t|"
            r"is mandatory|make sure|see to it|kindly ensure|no need to)\b",
            re.I,
        ),
        2,
    ),
    (
        "approval",
        re.compile(
            r"\b(?:approval|approver|approve[sd]?|authoris|authoriz|sign[- ]?off|"
            r"seek assistance|escalat|refer to the market|market counterpart|"
            r"team lead|supervisor|confirmation from|advise from)\b",
            re.I,
        ),
        3,
    ),
    (
        "exception",
        re.compile(
            r"\b(?:exception|rework|error|discrepanc|mismatch|does ?n[o\']t match|"
            r"doesn’t match|fail(?:ed|ure|s)?|reject|invalid|incorrect|"
            r"missing|blocked|block(?:ing)?|dispute|issue|problem|"
            r"marked for deletion|disregard)\b",
            re.I,
        ),
        2,
    ),
    (
        "mapping",
        re.compile(
            r"(\bZ[A-Z]{2,3}\d?\b|\bVA0[123]\b|\bFBL5N\b|\bOAR\b"
            r"|\breason code\b|\border type\b|\bbilling block\b|\bdoc(?:ument)? type\b"
            r"|\bsold[- ]?to\b|\bship[- ]?to\b|\bpayer\b|\bdistribution channel\b"
            r"|\bexternal reference\b|\bUOM\b|\bconvert(?:s|ed|ion)?\b|->|→"
            r"|\baccount ?#? ?\d{6,}\b|\bstatus \d{1,2}\b)",
            re.I,
        ),
        3,
    ),
    (
        "account_specific",
        re.compile(
            r"\b(?:Sobey|Fed[- ]?Coop|Federated Co[- ]?Operative|Grocery People|"
            r"GFS|Gordon Food|Rexall|Starbucks|Costco|Walmart|Loblaw|Metro|"
            r"Hopewell|Versacold|Vitality|NHS|ice ?cream|pizza)\w*\b",
            re.I,
        ),
        3,
    ),
    (
        "timing_sla",
        re.compile(
            r"\b(?:SLA|turnaround|cut[- ]?off|business day|working day|within \d+|"
            r"deadline|due date|ag[e]?ing|FIFO|end of (?:day|month))\b",
            re.I,
        ),
        2,
    ),
    (
        "tribal",
        re.compile(
            r"\b(?:aligned with|action crafted|work[- ]?around|for us to remind|"
            r"as agreed|was agreed|usually|commonly|normally|in practice|"
            r"is not around|not available|no longer available|back[- ]?up processor|"
            r"he may not be familiar|she may not be familiar|kindly inform|"
            r"this information is indicated here only|historically|"
            r"the reason behind is|reason behind)\b",
            re.I,
        ),
        4,
    ),
]

# Parameters worth lifting out of the statement so a register can key on them.
PARAM_PATTERNS = OrderedDict(
    [
        ("money", re.compile(r"\$\s?\d[\d,\.]*|\b\d[\d,]*\s?(?:CAD|USD|EUR|PHP)\b", re.I)),
        ("count", re.compile(r"\b\d+\s?(?:cases|days|hours|characters|digits|%)\b", re.I)),
        ("order_type", re.compile(r"\bZ[A-Z]{2,3}\d?\b")),
        ("billing_block", re.compile(r"\bbilling block\b[^.;|]{0,40}?\b(0[0-9])\b", re.I)),
        ("account_no", re.compile(r"\b\d{7}\b")),
        ("txn_code", re.compile(r"\b(?:VA0[123]|FBL5N|OAR|VF0[123]|MM0[123])\b", re.I)),
        ("status", re.compile(r"\bstatus \d{1,2}\b", re.I)),
    ]
)

# Lines that are structure, not content.
NOISE = re.compile(
    r"^\s*(?:\|?\s*-{2,}\s*\|?|\[\[(?:IMAGE|EMBEDDED OBJECT)|!\[|<br\s*/?>|"
    r"\*?\d+ image\(s\) exported|custom:MSIP|AppVersion|TotalTime|ContentTypeId)",
    re.I,
)

# Boilerplate that matches a family but says nothing.
STOP_STATEMENTS = re.compile(
    r"^(?:n/?a|none|tbd|yes|no|note|notes|nb|see below|see above|as follows|"
    r"click execute|refer to the (?:below|above)|same as above)\W*$",
    re.I,
)


def split_statements(block: str):
    """Break a markdown block into candidate statements."""
    # Table cells and explicit line breaks are statement boundaries in this corpus.
    parts = re.split(r"\s*(?:<br\s*/?>|\|)\s*", block)
    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Split on sentence ends, but keep decimals and abbreviations intact.
        for sent in re.split(r"(?<=[.;:!?])\s+(?=[A-Z0-9\-•])", part):
            sent = re.sub(r"\s+", " ", sent).strip(" \t•-")
            if sent:
                out.append(sent)
    return out


def classify(statement: str):
    """Return (hits, total weight). Hits are ordered most-informative first, so the
    primary category of a statement that is both a threshold and a tribal-knowledge
    marker is the tribal one - that is the rarer and more actionable signal."""
    scored, weight = [], 0
    for name, rx, w in FAMILIES:
        if rx.search(statement):
            scored.append((w, name))
            weight += w
    scored.sort(key=lambda pair: -pair[0])
    return [name for _, name in scored], weight


def lift_params(statement: str):
    found = []
    for label, rx in PARAM_PATTERNS.items():
        for m in rx.findall(statement):
            val = m if isinstance(m, str) else next((x for x in m if x), "")
            val = val.strip()
            if val:
                found.append("%s=%s" % (label, val))
    # Preserve order, drop repeats.
    return "; ".join(list(dict.fromkeys(found)))


def norm_key(statement: str):
    return re.sub(r"[^a-z0-9]+", " ", statement.lower()).strip()


def mine_file(path: str, min_len: int, max_len: int):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    source_doc = os.path.basename(path)
    section = "(top)"
    rows = []

    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")

        m = re.match(r"^##\s+Embedded content:\s*(.+?)\s+<-\s", line)
        if m:
            source_doc = m.group(1).strip()
            section = "(embedded)"
            continue
        m = re.match(r"^#\s+(?:\[\w+\]\s+)?(.+\.(?:docx|xlsx|pptx|msg|pdf|doc|xls|ppt))\s*$", line, re.I)
        if m:
            source_doc = m.group(1).strip()
            continue
        m = re.match(r"^#{2,3}\s+(.+?)\s*$", line)
        if m:
            section = m.group(1).strip()
            continue

        if NOISE.match(line) or not line.strip():
            continue

        for stmt in split_statements(line):
            if not (min_len <= len(stmt) <= max_len):
                continue
            if STOP_STATEMENTS.match(stmt):
                continue
            hits, weight = classify(stmt)
            if not hits:
                continue
            rows.append(
                {
                    "category_guess": "|".join(hits),
                    "weight": weight,
                    "parameters": lift_params(stmt),
                    "statement": stmt,
                    "source_doc": source_doc,
                    "section": section,
                    "line": lineno,
                    "corpus_file": os.path.basename(path),
                }
            )
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mine business-rule candidates from an extracted SOP corpus.")
    ap.add_argument("inputs", nargs="+", help="markdown/text corpus files (deep_extract output)")
    ap.add_argument("-o", "--outdir", default="rules-mining")
    ap.add_argument("--min-len", type=int, default=25)
    ap.add_argument("--max-len", type=int, default=400)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    warned = False
    all_rows = []
    for path in args.inputs:
        if not os.path.isfile(path):
            print("WARNING: not a file, skipped: %s" % path, file=sys.stderr)
            warned = True
            continue
        rows = mine_file(path, args.min_len, args.max_len)
        if not rows:
            print("WARNING: no candidates found in %s" % path, file=sys.stderr)
            warned = True
        all_rows.extend(rows)

    if not all_rows:
        print("No candidates found in any input.", file=sys.stderr)
        return 1

    # Deduplicate on normalised text, keeping the first occurrence and counting repeats.
    seen = {}
    for row in all_rows:
        key = norm_key(row["statement"])
        if key in seen:
            seen[key]["occurrences"] += 1
        else:
            row["occurrences"] = 1
            seen[key] = row

    rows = sorted(
        seen.values(),
        key=lambda r: (-r["weight"], -r["occurrences"], r["source_doc"], r["line"]),
    )
    for i, row in enumerate(rows, 1):
        row["cand_id"] = "C-%03d" % i

    os.makedirs(args.outdir, exist_ok=True)

    fields = [
        "cand_id",
        "category_guess",
        "weight",
        "occurrences",
        "parameters",
        "statement",
        "source_doc",
        "section",
        "line",
        "corpus_file",
    ]
    csv_path = os.path.join(args.outdir, "rule_candidates.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    # Readable grouping, primary category = first family hit.
    by_cat = OrderedDict()
    for row in rows:
        cat = row["category_guess"].split("|")[0]
        by_cat.setdefault(cat, []).append(row)

    md_path = os.path.join(args.outdir, "rule_candidates.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Rule candidates\n\n")
        fh.write("%d deduplicated statements from %d corpus file(s).\n\n" % (len(rows), len(args.inputs)))
        fh.write("Each row is a *candidate*. Classification, splitting of compound rules and\n")
        fh.write("conflict detection are the model's job, not this script's.\n\n")
        for cat, items in by_cat.items():
            fh.write("\n## %s  (%d)\n\n" % (cat, len(items)))
            fh.write("| id | parameters | statement | source | line |\n")
            fh.write("|---|---|---|---|---|\n")
            for row in items:
                stmt = row["statement"].replace("|", "\\|")
                fh.write(
                    "| %s | %s | %s | %s | %s |\n"
                    % (row["cand_id"], row["parameters"] or "-", stmt, row["source_doc"], row["line"])
                )

    cat_counts = Counter(r["category_guess"].split("|")[0] for r in rows)
    doc_counts = Counter(r["source_doc"] for r in rows)
    param_counts = Counter()
    for r in rows:
        for chunk in r["parameters"].split(";"):
            chunk = chunk.strip()
            if chunk:
                param_counts[chunk.split("=")[0]] += 1

    sum_path = os.path.join(args.outdir, "mining_summary.md")
    with open(sum_path, "w", encoding="utf-8") as fh:
        fh.write("# Mining summary\n\n")
        fh.write("- corpus files: %d\n" % len(args.inputs))
        fh.write("- raw candidate statements: %d\n" % len(all_rows))
        fh.write("- after deduplication: %d\n" % len(rows))
        fh.write("- miner version: %s\n\n" % __version__)
        fh.write("## By category (primary hit)\n\n| category | count |\n|---|---|\n")
        for cat, n in cat_counts.most_common():
            fh.write("| %s | %d |\n" % (cat, n))
        fh.write("\n## By parameter type\n\n| parameter | statements |\n|---|---|\n")
        for p, n in param_counts.most_common():
            fh.write("| %s | %d |\n" % (p, n))
        fh.write("\n## By source document (top 30)\n\n| source | count |\n|---|---|\n")
        for doc, n in doc_counts.most_common(30):
            fh.write("| %s | %d |\n" % (doc, n))

    if not args.quiet:
        print("candidates=%d (raw %d)  outdir=%s" % (len(rows), len(all_rows), args.outdir))
        for cat, n in cat_counts.most_common():
            print("  %-16s %d" % (cat, n))

    return 2 if warned else 0


if __name__ == "__main__":
    sys.exit(main())
