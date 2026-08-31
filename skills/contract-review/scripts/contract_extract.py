#!/usr/bin/env python3
"""Extract everything a contract reviewer needs from a .docx:
body text, Word comments, tracked-changes presence, placeholder scan,
and headers/footers. Pure stdlib — no python-docx or pandoc needed.

Usage:
    python contract_extract.py "path/to/contract.docx" [-o outdir]

Writes to outdir (default: alongside the docx, suffix _extracted):
    contract_text.txt   - body paragraphs, one per line
    comments.md         - reviewer comments with author/date (if any)
    review_flags.md     - placeholders, tracked changes, blank signature hints
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

PLACEHOLDER_PATTERNS = [
    (re.compile(r"\[[^\]\n]{0,80}\]"), "square-bracket placeholder"),
    (re.compile(r"X{3,}"), "XXX placeholder"),
    (re.compile(r"_{4,}"), "blank underscore line"),
    (re.compile(r"\bTBD\b|\bTBC\b|\bto be (agreed|confirmed|determined)\b", re.I),
     "TBD/TBC"),
]


def para_text(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def extract(docx_path: Path, outdir: Path):
    z = zipfile.ZipFile(docx_path)
    names = set(z.namelist())
    outdir.mkdir(parents=True, exist_ok=True)

    # --- body text ---
    doc = ET.fromstring(z.read("word/document.xml"))
    paras = [para_text(p) for p in doc.iter(W + "p")]
    (outdir / "contract_text.txt").write_text("\n".join(paras), encoding="utf-8")

    # --- comments ---
    comment_lines = []
    if "word/comments.xml" in names:
        c = ET.fromstring(z.read("word/comments.xml"))
        for com in c.iter(W + "comment"):
            author = com.get(W + "author", "?")
            date = com.get(W + "date", "?")
            text = "".join(t.text or "" for t in com.iter(W + "t"))
            comment_lines.append(f"- **{author}** ({date}): {text}")
    (outdir / "comments.md").write_text(
        "# Reviewer comments\n\n" + ("\n".join(comment_lines) or "None found."),
        encoding="utf-8")

    # --- review flags ---
    flags = []
    body_xml = z.read("word/document.xml").decode("utf-8", "ignore")
    n_ins = body_xml.count("<w:ins ")
    n_del = body_xml.count("<w:del ")
    if n_ins or n_del:
        flags.append(f"- **Unaccepted tracked changes**: {n_ins} insertions, "
                     f"{n_del} deletions still in the document.")
    if comment_lines:
        flags.append(f"- **Unresolved comments**: {len(comment_lines)} comment(s) "
                     "still attached (see comments.md). Resolve/strip before signature.")

    for i, txt in enumerate(paras, 1):
        for pat, label in PLACEHOLDER_PATTERNS:
            for m in pat.finditer(txt):
                snippet = txt.strip()[:100]
                flags.append(f"- **{label}** at paragraph {i}: `{m.group(0)[:40]}` "
                             f"in “{snippet}”")

    # headers/footers often carry stale titles or DRAFT marks
    for name in sorted(names):
        if re.match(r"word/(header|footer)\d*\.xml", name):
            hf = ET.fromstring(z.read(name))
            text = " ".join(filter(None, (t.text for t in hf.iter(W + "t")))).strip()
            if text:
                flags.append(f"- header/footer `{name}`: “{text[:120]}”")

    (outdir / "review_flags.md").write_text(
        "# Pre-signature hygiene flags\n\n" + ("\n".join(flags) or "None found."),
        encoding="utf-8")

    print(f"Extracted {len(paras)} paragraphs, {len(comment_lines)} comments, "
          f"{len(flags)} flags -> {outdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("-o", "--outdir")
    args = ap.parse_args()
    src = Path(args.docx)
    if not src.exists():
        sys.exit(f"Not found: {src}")
    outdir = Path(args.outdir) if args.outdir else src.with_suffix("") .parent / (
        src.stem + "_extracted")
    extract(src, outdir)


if __name__ == "__main__":
    main()
