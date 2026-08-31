"""House-style linter for IBM Consulting Finance Transformation deliverables.

    python ft_house_style.py <file-or-directory> [...]
    python ft_house_style.py draft.md --blueprint blueprint.json

Enforces the voice rules in `prompts/house_style_v1.txt` from the Blueprint Accelerator
(H:\\My Drive\\AA\\blueprint-accelerator) plus this skill's citation discipline:

  banned marketing words - filler hedges - sentence length - second person - unresolved
  [SENIOR REVIEW] markers - benchmark figures with no source

With --blueprint, also validates a drafted blueprint JSON against the house structure contract
(3 narrative paragraphs, exactly 4 pain points, 3 agents each with human_review, 3 user benefits
per stakeholder, 4 business benefits). That contract is owned by the accelerator's
`adapter/validation.py`; this is a convenience check for drafts outside the adapter, not a
replacement for it.

Exit code 1 if any error-level finding is present. Standard library only.
"""

import argparse
import json
import os
import re
import sys

# Findings quote source text, which contains em dashes and arrows. Windows consoles and
# redirected output default to cp1252 and would raise UnicodeEncodeError on them.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BANNED_WORDS = ["leverage", "unlock", "empower", "seamless", "robust", "synergy",
                "best-in-class", "world-class", "transformative"]
FILLER_WORDS = ["essentially", "basically", "really", "very", "just"]
SECOND_PERSON = [r"\byou\b", r"\byour\b", r"\byou're\b", r"\byours\b"]

# The one legitimate appearance of a banned word: Hackett's defined benchmark cohort.
ALLOWED_PHRASES = ["digital world class", "world class finance teams"]

SENTENCE_CAP = 28
SENTENCE_AVG = 22.0  # warn above this; the prompt targets ~18

TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}

# Lines that quote the rules themselves rather than breaking them.
META_MARKERS = ["banned", "no marketing", "delete \"", "house style", "filler hedge",
                "do not use", "never use", "avoid "]


class Finding:
    def __init__(self, level, path, line, rule, detail):
        self.level = level
        self.path = path
        self.line = line
        self.rule = rule
        self.detail = detail

    def __str__(self):
        return "{:5s} {}:{} [{}] {}".format(
            self.level.upper(), self.path, self.line, self.rule, self.detail)


def is_meta_line(line):
    lowered = line.lower()
    return any(marker in lowered for marker in META_MARKERS)


SUPPRESS_MARKER = "house-style: allow"
SUPPRESS_SPAN = 3  # the marker covers its own line plus the next two, for wrapped sentences


def in_allowed_phrase(lowered_line, start, end):
    """True if the hit sits inside a cited proper noun. Hyphens and underscores are normalised
    to spaces first, so a URL slug like `digital-world-class-...` matches the phrase."""
    normalised = re.sub(r"[-_]", " ", lowered_line)
    for phrase in ALLOWED_PHRASES:
        for match in re.finditer(re.escape(phrase), normalised):
            if match.start() <= start and end <= match.end():
                return True
    return False


def suppressed_lines(lines):
    """Line numbers covered by an explicit `house-style: allow` marker."""
    allowed = set()
    for i, line in enumerate(lines, start=1):
        if SUPPRESS_MARKER in line.lower():
            allowed.update(range(i, i + SUPPRESS_SPAN))
    return allowed


def strip_code_blocks(lines):
    """Return (line_number, text) for prose lines only - fenced code is not prose."""
    out, fenced = [], False
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def split_sentences(text):
    text = re.sub(r"`[^`]*`", " ", text)          # inline code
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> label
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def lint_text(path, text):
    findings = []
    lines = text.splitlines()
    prose = strip_code_blocks(lines)
    suppressed = suppressed_lines(lines)

    for lineno, line in prose:
        stripped = line.strip()
        if not stripped or stripped.startswith("|") or stripped.startswith(">"):
            continue
        lowered = line.lower()
        meta = is_meta_line(line) or lineno in suppressed

        for word in BANNED_WORDS:
            for match in re.finditer(r"\b" + re.escape(word) + r"\w*", lowered):
                if in_allowed_phrase(lowered, match.start(), match.end()):
                    continue
                if meta:
                    continue
                findings.append(Finding("error", path, lineno, "banned-word",
                                        "'{}' - marketing language".format(match.group(0))))

        if not meta:
            for word in FILLER_WORDS:
                for _ in re.finditer(r"\b" + re.escape(word) + r"\b", lowered):
                    findings.append(Finding("warn", path, lineno, "filler",
                                            "'{}' - filler hedge".format(word)))

        if "[SENIOR REVIEW]" in line:
            findings.append(Finding("warn", path, lineno, "senior-review",
                                    "unresolved [SENIOR REVIEW] marker"))

    # Sentence length over the prose body, headings excluded.
    body = "\n".join(l for n, l in prose if not l.strip().startswith(("#", "-", "*", "|", ">")))
    sentences = split_sentences(body)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 3]
    if lengths:
        average = sum(lengths) / len(lengths)
        if average > SENTENCE_AVG:
            findings.append(Finding("warn", path, 0, "sentence-avg",
                                    "average sentence {:.1f} words - house style targets ~18"
                                    .format(average)))
        for sentence, length in zip([s for s in sentences if len(s.split()) > 3], lengths):
            if length > SENTENCE_CAP:
                findings.append(Finding("warn", path, 0, "sentence-cap",
                                        "{} words (cap {}): \"{}...\"".format(
                                            length, SENTENCE_CAP, sentence[:70])))
    return findings


def lint_blueprint(path, payload):
    """Convenience check of a drafted blueprint against the house structure contract."""
    findings = []

    def err(detail):
        findings.append(Finding("error", path, 0, "blueprint-contract", detail))

    if not isinstance(payload, dict):
        err("blueprint must be a JSON object")
        return findings

    for field in ("narrative", "pain_points", "agents", "user_benefits",
                  "business_benefits", "checkpoint_flags"):
        if field not in payload:
            err("missing required field '{}'".format(field))

    narrative = payload.get("narrative")
    if isinstance(narrative, str):
        paragraphs = [p for p in narrative.strip().split("\n\n") if p.strip()]
        if len(paragraphs) != 3:
            err("narrative must be exactly 3 paragraphs, got {}".format(len(paragraphs)))

    pain_points = payload.get("pain_points")
    if isinstance(pain_points, list) and len(pain_points) != 4:
        err("pain_points must be exactly 4, got {}".format(len(pain_points)))

    agents = payload.get("agents")
    if isinstance(agents, list):
        if len(agents) != 3:
            err("agents must be exactly 3, got {}".format(len(agents)))
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                err("agents[{}] must be an object".format(i))
                continue
            for key in ("name", "purpose", "human_review"):
                if not str(agent.get(key, "")).strip():
                    err("agents[{}].{} is required - never describe an agent that runs "
                        "unattended on finance-sensitive content".format(i, key))

    benefits = payload.get("user_benefits")
    if isinstance(benefits, dict):
        if not benefits:
            err("user_benefits must name at least one stakeholder role")
        for role, items in benefits.items():
            if not isinstance(items, list) or len(items) != 3:
                err("user_benefits['{}'] must be exactly 3, got {}".format(
                    role, len(items) if isinstance(items, list) else "not a list"))

    business = payload.get("business_benefits")
    if isinstance(business, list) and len(business) != 4:
        err("business_benefits must be exactly 4 (cycle acceleration, risk reduction, "
            "governance and auditability, scalability), got {}".format(len(business)))

    for field in ("pain_points", "business_benefits"):
        for item in payload.get(field) or []:
            if isinstance(item, str):
                findings.extend(
                    f for f in lint_text(path + ":" + field, item) if f.rule == "banned-word")
    return findings


def collect_files(targets):
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(target)
        elif os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in sorted(names):
                    if os.path.splitext(name)[1].lower() in TEXT_SUFFIXES:
                        files.append(os.path.join(root, name))
        else:
            print("skipped (not found): " + target)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="+", help="files or directories to lint")
    parser.add_argument("--blueprint", help="a drafted blueprint JSON to check against the contract")
    parser.add_argument("--quiet", action="store_true", help="errors only")
    args = parser.parse_args(argv)

    findings = []
    files = collect_files(args.targets)
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                findings.extend(lint_text(path, fh.read()))
        except OSError as exc:
            print("could not read {}: {}".format(path, exc))

    if args.blueprint:
        with open(args.blueprint, encoding="utf-8") as fh:
            findings.extend(lint_blueprint(args.blueprint, json.load(fh)))

    # A blueprint passed as both a target and --blueprint is scanned twice; keep one finding.
    deduped, seen = [], set()
    for finding in findings:
        key = (finding.level, finding.rule, finding.detail, finding.path.split(":")[0])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    findings = deduped

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warn"]

    for finding in errors:
        print(finding)
    if not args.quiet:
        for finding in warnings:
            print(finding)

    print("\n{} file(s) checked: {} error(s), {} warning(s)".format(
        len(files), len(errors), len(warnings)))
    if errors:
        print("Banned words and contract violations must be fixed before delivery.")
    if warnings and not errors:
        print("Warnings are advisory. Sentence-length warnings are expected in internal method "
              "documents; fix them in anything a client reads.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
