#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract.py - one entry point for every document-extraction profile.

This is a dispatcher, not a parser. It owns no extraction logic; each profile
runs the script that already implements it, so nothing is duplicated and a fix
in the underlying skill takes effect here immediately.

    extract.py deep     <file> [-o OUT] [--max-depth N] [--no-media]
                               [--max-text-mb N] [--quiet]
        Everything, recursively, including files embedded inside files.
        -> deep-extract

    extract.py contract <docx> [-o OUT]
        Reviewer's three files: body text, comments, pre-signature flags.
        -> contract-review

    extract.py corpus   inventory|extract|fit|check --in DIR --out DIR
                                                    [--cap-mb N]
        Make a corpus ingestible under a file-size cap.
        -> corpus-prep-for-ingestion

    extract.py all      <docx> [-o OUT]
        deep + contract over one document, into OUT/deep and OUT/contract,
        with a combined _SUMMARY.md.

    extract.py where
        Show which script each profile resolved to. Use this first when a
        profile reports a missing skill.

Exit codes are uniform across profiles: 0 clean, 2 finished with warnings
(damaged container, missing embedded parts, reductions), 1 failed.
"""

import argparse
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _locate

PROFILE_SKILL = {"deep": "deep-extract",
                 "contract": "contract-review",
                 "corpus": "corpus-prep-for-ingestion"}


def run(profile, args, capture=False):
    """Invoke the owning script with the current interpreter."""
    script = _locate.find(profile)
    cmd = [sys.executable, script] + list(args)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if capture:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        return r.returncode, (r.stdout or "")
    return subprocess.call(cmd, env=env), ""


def cmd_where(_):
    resolved = _locate.resolve_all()
    width = max(len(p) for p in resolved)
    missing = 0
    for profile, path in sorted(resolved.items()):
        if path:
            print("  %-*s  %s" % (width, profile, path))
        else:
            missing += 1
            print("  %-*s  NOT FOUND - needs the `%s` skill"
                  % (width, profile, PROFILE_SKILL[profile]))
    if missing:
        print("\n%d profile(s) unavailable. Install the named skill(s) in the "
              "same skills directory as `extract`." % missing)
    return 2 if missing else 0


def cmd_deep(a, rest):
    args = [a.file]
    if a.outdir:
        args += ["-o", a.outdir]
    return run("deep", args + rest)[0]


def cmd_contract(a, rest):
    args = [a.file]
    if a.outdir:
        args += ["-o", a.outdir]
    return run("contract", args + rest)[0]


def cmd_corpus(a, rest):
    return run("corpus", [a.step] + rest)[0]


def cmd_all(a, rest):
    src = os.path.abspath(a.file)
    out = os.path.abspath(a.outdir or (os.path.splitext(src)[0] + "_extracted"))
    deep_dir = os.path.join(out, "deep")
    con_dir = os.path.join(out, "contract")
    os.makedirs(deep_dir, exist_ok=True)
    os.makedirs(con_dir, exist_ok=True)

    print("=" * 70)
    print("deep profile")
    rc_deep, out_deep = run("deep", [src, "-o", deep_dir, "--quiet"] + rest,
                            capture=True)
    print("=" * 70)
    print("contract profile")
    rc_con, out_con = run("contract", [src, "-o", con_dir], capture=True)

    with io.open(os.path.join(out, "_SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write("# Extraction summary\n\nSource: `%s`\n\n" % src)
        fh.write("| profile | exit | output |\n|---|---|---|\n")
        fh.write("| deep | %d | `deep/` |\n" % rc_deep)
        fh.write("| contract | %d | `contract/` |\n\n" % rc_con)
        if 2 in (rc_deep, rc_con):
            fh.write("> Exit code 2 means the run finished **with warnings** - "
                     "a damaged container, missing embedded parts, or a "
                     "reduction. Read `deep/_ALL_TEXT.md` and "
                     "`contract/review_flags.md` before treating the "
                     "extraction as complete.\n\n")
        for label, text in (("deep", out_deep), ("contract", out_con)):
            fh.write("## %s output\n\n```\n%s\n```\n\n" % (label, text.strip()))

    print("=" * 70)
    print("combined summary -> %s" % os.path.join(out, "_SUMMARY.md"))
    return 2 if 2 in (rc_deep, rc_con) else max(rc_deep, rc_con)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("deep", help="recursive full extraction")
    p.add_argument("file")
    p.add_argument("-o", "--outdir")
    p.set_defaults(func=cmd_deep)

    p = sub.add_parser("contract", help="contract reviewer's three files")
    p.add_argument("file")
    p.add_argument("-o", "--outdir")
    p.set_defaults(func=cmd_contract)

    p = sub.add_parser("corpus", help="corpus prep for an ingestion cap")
    p.add_argument("step", choices=["inventory", "extract", "fit", "check"])
    p.set_defaults(func=cmd_corpus)

    p = sub.add_parser("all", help="deep + contract over one document")
    p.add_argument("file")
    p.add_argument("-o", "--outdir")
    p.set_defaults(func=cmd_all)

    p = sub.add_parser("where", help="show which script each profile resolves to")
    p.set_defaults(func=lambda a, rest: cmd_where(a))

    args, rest = ap.parse_known_args()
    try:
        return args.func(args, rest)
    except _locate.Missing as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
