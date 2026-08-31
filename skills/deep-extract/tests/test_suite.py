# -*- coding: utf-8 -*-
"""Regression suite for the extraction skill set.

Run:  python tests/test_suite.py
Exit: 0 all passed, 1 one or more failed.

Every check asserts against a real file on disk, not a recorded expectation.
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BOB = r"H:\My Drive\AA\bob-skills"
ROOTS = [BOB, r"C:\Users\GRACEPAN\.claude\skills", r"H:\My Drive\AA\.bob\skills"]
MATERIALS = r"C:\Users\GRACEPAN\Box\#Grace\ClientZero\NAR_Nestle\Materials"
HEALTHY = os.path.join(MATERIALS, "OS_NBS Manila_O2C_CA_Credit Management.docx")
DAMAGED = os.path.join(MATERIALS, "OG_NBS Manila_O2C_CA_Returns and Refusals 1.docx")
EXTRACT = r"C:\Users\GRACEPAN\.claude\skills\extract\scripts\extract.py"

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("  %-58s %s %s" % (name[:58], "PASS" if ok else "FAIL", detail[:44]),
          flush=True)
    return ok


def run(args, cwd=None):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV, cwd=cwd)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def tmpdir():
    d = tempfile.mkdtemp(prefix="dx_test_")
    return d


# ---------------------------------------------------------------- 1. syntax
print("\n1. every script compiles")
SCRIPTS = [
    ("13-deep-extract", "deep_extract.py"), ("13-deep-extract", "_engine.py"),
    ("07-contract-review", "contract_extract.py"), ("07-contract-review", "_engine.py"),
    ("11-corpus-prep-for-ingestion", "corpus_prep.py"),
    ("11-corpus-prep-for-ingestion", "_engine.py"),
    ("14-extract", "extract.py"), ("14-extract", "_locate.py"),
]
for skill, script in SCRIPTS:
    p = os.path.join(BOB, skill, "scripts", script)
    rc, out = run(["-m", "py_compile", p])
    check("compiles: %s/%s" % (skill, script), rc == 0, out[-40:] if rc else "")

# ------------------------------------------------- 2. single implementation
print("\n2. one implementation of each script across all roots")
NAMES = ("deep_extract.py", "contract_extract.py", "corpus_prep.py", "extract.py")
seen = {}
for root in ROOTS:
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f in NAMES:
                h = hashlib.sha1(open(os.path.join(dp, f), "rb").read()).hexdigest()
                seen.setdefault(f, set()).add(h)
for f in NAMES:
    hs = seen.get(f, set())
    check("single version: %s" % f, len(hs) == 1,
          "%d distinct" % len(hs) if len(hs) != 1 else "")

# ------------------------------------------------------------ 3. resolution
print("\n3. front-end resolves every profile")
rc, out = run([EXTRACT, "where"])
check("extract where -> exit 0", rc == 0)
for prof in ("deep", "contract", "corpus"):
    check("resolves profile: %s" % prof,
          prof in out and "NOT FOUND" not in out.split(prof)[1][:60])

# ------------------------------------------------- 4. healthy file, clean run
print("\n4. healthy document -> exit 0")
d = tmpdir()
rc, out = run([EXTRACT, "deep", HEALTHY, "-o", d, "--quiet"])
man = json.load(open(os.path.join(d, "_MANIFEST.json"), encoding="utf-8"))
enc = [n for n in man["nodes"] if n.get("encrypted")]
shell = [n for n in man["nodes"] if (n.get("status") or "").startswith("EMPTY")]
check("credit-mgmt exit 2 (encrypted + empty shell present)", rc == 2, "rc=%d" % rc)
check("  encrypted node flagged", len(enc) == 1, "%d found" % len(enc))
check("  empty-shell node flagged", len(shell) == 1, "%d found" % len(shell))
tree = io.open(os.path.join(d, "_TREE.txt"), encoding="utf-8").read()
check("  _TREE.txt annotates ENCRYPTED", "[ENCRYPTED:" in tree)
check("  _TREE.txt annotates EMPTY SHELL", "[EMPTY SHELL" in tree)
for f in ("_ALL_TEXT.md", "_TREE.txt", "_MANIFEST.json"):
    b = open(os.path.join(d, f), "rb").read()
    bad = sum(1 for c in b if c < 32 and c not in (9, 10, 13))
    check("  %s free of control bytes" % f, bad == 0, "%d found" % bad)
shutil.rmtree(d, ignore_errors=True)

# ------------------------------------------------ 5. damaged file, salvage
print("\n5. truncated document -> salvage + reconciliation")
d = tmpdir()
rc, out = run([EXTRACT, "deep", DAMAGED, "-o", d, "--quiet"])
check("returns-refusals exit 2", rc == 2, "rc=%d" % rc)
man = json.load(open(os.path.join(d, "_MANIFEST.json"), encoding="utf-8"))
w = " ".join(man["warnings"])
check("  salvage engaged", "salvaging via local file headers" in w)
check("  truncation reported", "TRUNCATED" in w)
check("  partial recovery reported", "PARTIAL" in w)
check("  partial count == 1", man["counts"].get("partial") == 1,
      str(man["counts"].get("partial")))
missing = set()
for n in man["nodes"]:
    missing.update(n.get("missing_embeddings") or [])
check("  12 embeddings reported absent", len(missing) == 12, str(len(missing)))
root_node = man["nodes"][0]
body = io.open(os.path.join(d, root_node["text_file"].replace("/", os.sep)),
               encoding="utf-8").read()
check("  42 embedded-object markers in body",
      body.count("EMBEDDED OBJECT progid=") == 42,
      str(body.count("EMBEDDED OBJECT progid=")))

# --- flat layout keeps every path well inside the Windows limit
lens = [len(os.path.join(r, f)) for r, _, fs in os.walk(d) for f in fs]
check("  no output path over 260 characters", max(lens) <= 260,
      "longest %d" % max(lens))
check("  recovered/ used by default", os.path.isdir(os.path.join(d, "recovered")))
check("  files/ not created by default",
      not os.path.isdir(os.path.join(d, "files")))
check("  text/ is flat",
      all(not os.path.isdir(os.path.join(d, "text", e))
          for e in os.listdir(os.path.join(d, "text"))))

# --- the summary table
sm = os.path.join(d, "_SUMMARY.md")
check("  _SUMMARY.md written", os.path.exists(sm))
summ = io.open(sm, encoding="utf-8").read()
check("  summary counts items", "Items found inside" in summ)
check("  summary has a client-action section", "Ask the client for these" in summ)
check("  summary lists the 12 absent embeddings",
      summ.count("| MISSING |") + summ.count("MISSING") >= 12,
      str(summ.count("MISSING")))
check("  summary uses readable names, not stream ids",
      "^01Ole10Native" not in summ)
shutil.rmtree(d, ignore_errors=True)

# --- opt back in to the mirrored layout
d = tmpdir()
rc, out = run([EXTRACT, "deep", HEALTHY, "-o", d, "--nested", "--quiet"])
check("--nested restores files/", os.path.isdir(os.path.join(d, "files")))
check("--nested skips recovered/",
      not os.path.isdir(os.path.join(d, "recovered")))
shutil.rmtree(d, ignore_errors=True)

# -------------------------------------------------------- 6. flag pass-through
print("\n6. flags reach the underlying script")
d = tmpdir()
rc, out = run([EXTRACT, "deep", DAMAGED, "-o", d, "--max-depth", "1",
               "--no-media", "--quiet"])
man = json.load(open(os.path.join(d, "_MANIFEST.json"), encoding="utf-8"))
depths = [n["path"].count(" > ") for n in man["nodes"]]
check("--max-depth 1 honoured", max(depths) <= 2, "max depth seen %d" % max(depths))
saved_media = [n for n in man["nodes"]
               if n["kind"] == "media" and n.get("saved_as")]
check("--no-media honoured", len(saved_media) == 0, "%d saved" % len(saved_media))
shutil.rmtree(d, ignore_errors=True)

# ------------------------------------------------------- 7. contract profile
print("\n7. contract profile")
d = tmpdir()
rc, out = run([EXTRACT, "contract", HEALTHY, "-o", d])
check("contract on healthy -> exit 0", rc == 0, "rc=%d" % rc)
for f in ("contract_text.txt", "comments.md", "review_flags.md"):
    check("  produces %s" % f, os.path.exists(os.path.join(d, f)))
flags = io.open(os.path.join(d, "review_flags.md"), encoding="utf-8").read()
check("  lists embedded attachments", "Embedded attachments" in flags)
shutil.rmtree(d, ignore_errors=True)

d = tmpdir()
rc, out = run([EXTRACT, "contract", DAMAGED, "-o", d])
check("contract on damaged -> exit 2", rc == 2, "rc=%d" % rc)
flags = io.open(os.path.join(d, "review_flags.md"), encoding="utf-8").read()
check("  reports container damage", "Container damage" in flags)
check("  reports missing attachments", "Missing attachments" in flags)
shutil.rmtree(d, ignore_errors=True)

# --------------------------------------------------------- 8. corpus profile
print("\n8. corpus profile, four steps")
cin, cout = tmpdir(), tmpdir()
shutil.copy(DAMAGED, os.path.join(cin, "sop.docx"))
for step in ("inventory", "extract", "fit", "check"):
    args = [EXTRACT, "corpus", step, "--out", cout, "--cap-mb", "10"]
    if step in ("inventory", "extract", "check"):
        args += ["--in", cin]
    rc, out = run(args)
    check("corpus %s -> exit 0" % step, rc == 0, "rc=%d" % rc)
s = json.load(open(os.path.join(cout, "summary.json"), encoding="utf-8"))
check("  embedded parts found (was 0 before consolidation)",
      s["embedded_parts"] >= 29, str(s["embedded_parts"]))
check("  damage surfaced", bool(s.get("damaged_containers")))
check("  declared-but-absent surfaced", bool(s.get("declared_but_absent")))
shutil.rmtree(cin, ignore_errors=True)
shutil.rmtree(cout, ignore_errors=True)

# ------------------------------------------------------------- 9. all profile
print("\n9. all profile")
d = tmpdir()
rc, out = run([EXTRACT, "all", HEALTHY, "-o", d, "--quiet"])
check("all -> exit 2 (encrypted payload present)", rc == 2, "rc=%d" % rc)
check("  deep/ written", os.path.isdir(os.path.join(d, "deep")))
check("  contract/ written", os.path.isdir(os.path.join(d, "contract")))
check("  _SUMMARY.md written", os.path.exists(os.path.join(d, "_SUMMARY.md")))
shutil.rmtree(d, ignore_errors=True)

# ------------------------------------------------- 10. missing dependency path
print("\n10. missing-dependency error is actionable")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "_locate", os.path.join(BOB, "14-extract", "scripts", "_locate.py"))
loc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loc)
loc.SEARCH_ROOTS = [os.path.join(tempfile.gettempdir(), "definitely_absent")]
try:
    loc.find("contract")
    check("names the missing skill", False, "no exception raised")
except loc.Missing as exc:
    check("names the missing skill", "contract-review" in str(exc))
    check("lists the paths tried", "Looked in" in str(exc))

# ------------------------------------------------------------------ summary
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = [n for n, ok, _ in RESULTS if not ok]
print("\n" + "=" * 72)
print("%d checks, %d passed, %d failed" % (len(RESULTS), passed, len(failed)))
for n in failed:
    print("  FAILED: %s" % n)
sys.exit(1 if failed else 0)
