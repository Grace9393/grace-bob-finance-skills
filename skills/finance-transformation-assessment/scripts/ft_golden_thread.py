"""Golden thread taxonomy lookup, scoping and blueprint drafting queue.

    python ft_golden_thread.py list  [--thread RTR] [--section 1.8] [--area OTC] [--search close]
    python ft_golden_thread.py scope 1.7 1.8 3.7 3.9
    python ft_golden_thread.py queue <initiative-backlog.csv> [--register <pain-point-register.csv>]

The taxonomy is `assets/golden-thread-taxonomy.csv` — 220 steps across RTR (73), S2P (59) and
OTC (88), generated from the prototype sources. See `references/golden-threads.md` for the
framework, the modal-to-blueprint conversion deltas, and which source documents are trustworthy.

Standard library only.
"""

import argparse
import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TAXONOMY = os.path.join(HERE, "..", "assets", "golden-thread-taxonomy.csv")


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def sort_key(step):
    return [int(part) for part in step.split(".")]


def matches_scope(step_row, scope):
    """A scope token is a thread (RTR), a section (1.8) or a full step (1.8.3)."""
    for token in scope:
        token = token.strip()
        if not token:
            continue
        if token.upper() == step_row["thread"]:
            return True
        if step_row["step"] == token or step_row["section"] == token:
            return True
        if step_row["step"].startswith(token + "."):
            return True
    return False


def run_list(args):
    rows = load(args.taxonomy)
    if args.thread:
        rows = [r for r in rows if r["thread"].upper() == args.thread.upper()]
    if args.section:
        rows = [r for r in rows if r["section"] == args.section
                or r["step"].startswith(args.section + ".")]
    if args.area:
        rows = [r for r in rows if r["process_area"].upper() == args.area.upper()]
    if args.search:
        needle = args.search.lower()
        rows = [r for r in rows if needle in r["step_title"].lower()
                or needle in r["section_title"].lower()]

    if not rows:
        print("no steps matched")
        return 0

    current = None
    for row in sorted(rows, key=lambda r: sort_key(r["step"])):
        if row["section"] != current:
            current = row["section"]
            area = row["process_area"] or "NO PROCESS AREA"
            print("\n{} {} — {}  [process area: {} | assessment: {}]".format(
                row["thread"], row["section"], row["section_title"], area, row["assessment_l2"]))
        flag = "" if row["title_source"] == "prototype" else "   << title not captured"
        print("  {:8s} {}{}".format(row["step"], row["step_title"], flag))
    print("\n{} step(s)".format(len(rows)))
    return 0


def run_scope(args):
    rows = load(args.taxonomy)
    in_scope = [r for r in rows if matches_scope(r, args.scope)]
    if not in_scope:
        print("nothing matched {} — scope tokens are a thread (RTR), a section (1.8) or a step "
              "(1.8.3)".format(args.scope))
        return 1

    by_section = {}
    for row in in_scope:
        by_section.setdefault((row["thread"], row["section"], row["section_title"]), []).append(row)

    print("# Engagement scope — golden thread steps\n")
    print("| Thread | Section | Steps | Process area | Assessment L2 |")
    print("|---|---|---|---|---|")
    no_area, pending = [], []
    for (thread, section, title), steps in sorted(
            by_section.items(), key=lambda kv: sort_key(kv[0][1])):
        area = steps[0]["process_area"]
        print("| {} | {} {} | {} | {} | {} |".format(
            thread, section, title, len(steps), area or "**none**", steps[0]["assessment_l2"]))
        if not area:
            no_area.append("{} {} {}".format(thread, section, title))
        pending += [s for s in steps if s["title_source"] != "prototype"]

    total = len(in_scope)
    print("\n**{} steps in scope** across {} section(s).".format(total, len(by_section)))

    print("\n## Assessment mapping\n")
    print("Benchmark (Phase 2) and score (Phase 3) against these assessment L2 processes: "
          + ", ".join(sorted({r["assessment_l2"] for r in in_scope if r["assessment_l2"]})))
    print("\nTag every pain point register row with its `step` so findings and modals reconcile.")

    if no_area:
        print("\n## Checkpoint flag — scope outside the blueprint process-area enum\n")
        for item in no_area:
            print("- {}".format(item))
        print("\nThese sections can be assessed, benchmarked and roadmapped, but **cannot be "
              "drafted as blueprints** until the closed enum is extended (that requires the system "
              "prompt, validator, ICA prompt and benchmark scenarios to change in one commit). "
              "Raise this at scoping, not at drafting.")

    if pending:
        print("\n## Warning — {} step title(s) never captured from the prototype\n".format(len(pending)))
        for row in pending[:15]:
            print("- {} (section {})".format(row["step"], row["section"]))
        if len(pending) > 15:
            print("- ... and {} more".format(len(pending) - 15))
        print("\nRecover these from the running prototype. Do NOT substitute names from "
              "`IBM_OTC_AI_UseCases_Complete_88Modals` or `IBM_OTC_MASTER_DOCUMENT_88Modals` — "
              "their step names do not match the prototype (golden-threads.md 7).")
    return 0


def run_queue(args):
    taxonomy = load(args.taxonomy)
    by_step = {r["step"]: r for r in taxonomy}
    by_area = {}
    for row in taxonomy:
        by_area.setdefault(row["process_area"], []).append(row)

    initiatives = load(args.initiatives)
    register = load(args.register) if args.register else []
    pain_by_area, pain_by_id = {}, {}
    for row in register:
        area = (row.get("process_area") or "").strip()
        pain_by_area.setdefault(area, []).append(row)
        pain_by_id[(row.get("id") or "").strip()] = row

    def evidence_pool(initiative, area):
        """Pain points available for this blueprint: the initiative's own, plus same-area rows."""
        pool = {pid.strip() for pid in (initiative.get("pain_point_ids") or "").split(";")
                if pid.strip() in pain_by_id}
        pool |= {(r.get("id") or "").strip() for r in pain_by_area.get(area, []) if area}
        return sorted(pool)

    print("# Blueprint drafting queue\n")
    print("One use-case blueprint per agentic initiative, in wave order. Each needs a "
          "`process_area`, four evidenced pain points and the personas involved "
          "(house-style-and-blueprint-contract.md 2).\n")
    print("| Order | Wave | Initiative | Process area | Pain points available | Draftable |")
    print("|---|---|---|---|---|---|")

    queued, blocked = [], []
    ordered = sorted(initiatives, key=lambda i: (int(i.get("wave") or 9), i.get("id", "")))
    for position, initiative in enumerate(ordered, start=1):
        steps = [s.strip() for s in (initiative.get("golden_thread_steps") or "").split(";")
                 if s.strip()]
        areas = {by_step[s]["process_area"] for s in steps if s in by_step}
        area = next((a for a in areas if a), "")
        if not area:
            area = (initiative.get("process_area") or "").strip()
        pool = evidence_pool(initiative, area) if register else []
        available = "{} ({})".format(len(pool), ", ".join(pool)) if register else "-"
        draftable = "yes" if area else "NO - no process area"
        if register and area and len(pool) < 4:
            draftable = "not yet - {} of 4".format(len(pool))
        row = (position, initiative.get("wave", ""), initiative.get("name", ""), area or "none",
               available, draftable)
        print("| {} | {} | {} | {} | {} | {} |".format(*row))
        (queued if draftable == "yes" else blocked).append((initiative, draftable))

    print("\n**{} draftable now, {} blocked.**".format(len(queued), len(blocked)))
    if blocked:
        print("\n## Blocked\n")
        for initiative, reason in blocked:
            if reason.startswith("NO"):
                fix = ("no process area — the scope sits outside the closed enum "
                       "(golden-threads.md 8)")
            else:
                fix = ("the evidence pool holds fewer than the four pain points the contract "
                       "requires — go back to the register, not to invention")
            print("- `{}` {} — {}.".format(initiative.get("id"), initiative.get("name"), fix))
        print("\nA blueprint needs exactly four pain points and three user benefits per role. "
              "Where the register cannot supply them, raise a checkpoint flag stating what is "
              "missing. Never pad to hit a count.")
    print("\nAdd a `golden_thread_steps` column to the backlog (semicolon-separated step ids such "
          "as `3.7.2;3.7.6`) to map initiatives onto the thread automatically.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--taxonomy", default=DEFAULT_TAXONOMY)
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", parents=[common], help="browse the taxonomy")
    p_list.add_argument("--thread", help="RTR, S2P or OTC")
    p_list.add_argument("--section", help="e.g. 1.8")
    p_list.add_argument("--area", help="blueprint process area, e.g. OTC or R2R")
    p_list.add_argument("--search", help="match step or section title")
    p_list.set_defaults(func=run_list)

    p_scope = sub.add_parser("scope", parents=[common], help="scope an engagement to thread steps")
    p_scope.add_argument("scope", nargs="+", help="threads, sections or steps")
    p_scope.set_defaults(func=run_scope)

    p_queue = sub.add_parser("queue", parents=[common], help="blueprint drafting queue by wave")
    p_queue.add_argument("initiatives")
    p_queue.add_argument("--register", help="pain point register, to check evidence coverage")
    p_queue.set_defaults(func=run_queue)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
