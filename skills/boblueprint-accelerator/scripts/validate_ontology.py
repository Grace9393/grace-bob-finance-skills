#!/usr/bin/env python3
"""
validate_ontology.py — sanity-check a JSON-LD ontology against the
Context Studio shape conventions.

Exits 0 if the file is clean, 1 otherwise. Prints a numbered list of
problems suitable for showing to a user or feeding back to a coding
agent for refactoring.

Checks performed (each maps to a failure mode the ICA Context Studio
Lab calls out, or to a structural requirement of the Entity / Operation /
State pattern):

  1.  File is valid JSON.
  2.  File is UTF-8.
  3.  Top level is an object with @context and @graph and nothing else.
  4.  @context contains the two-namespace pattern (custom prefix + schema:).
  5.  @context defines the id and type shortcuts (@id, @type).
  6.  @context declares Entity, Operation, State as type aliases.
  7.  @context properties that should be IRI references carry
      "@type": "@id" — this is the single most common cause of
      "graph looks empty after import".
  8.  @graph is a non-empty array.
  9.  Every @graph member has id, type, name (the lab's required trio).
 10.  Every type is one of Entity, Operation, State.
 11.  Every Operation has from and to.
 12.  All id values are unique.
 13.  Every cross-reference (from, to, relatesTo, hasState, initialState,
      terminalStates, emitsEvent) resolves to an id present in @graph.
 14.  All id values use the declared custom prefix (catches typos).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CROSS_REF_FIELDS = (
    "from",
    "to",
    "relatesTo",
    "hasState",
    "initialState",
    "terminalStates",
    "emitsEvent",
)

VALID_TYPES = {"Entity", "Operation", "State"}

# Fields that, in @context, should be declared as IRI references because
# their values point to other @graph members. Missing "@type": "@id" on
# these is the canonical "empty graph after import" failure.
IRI_REFERENCE_FIELDS = (
    "from",
    "to",
    "relatesTo",
    "hasState",
    "initialState",
    "terminalStates",
    "emitsEvent",
)


class Problems:
    """Accumulates numbered problems and reports them."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, msg: str) -> None:
        self.items.append(msg)

    def __bool__(self) -> bool:
        return bool(self.items)

    def report(self) -> str:
        if not self.items:
            return "OK — ontology is clean."
        lines = [f"Found {len(self.items)} problem(s):"]
        for n, msg in enumerate(self.items, 1):
            lines.append(f"  {n}. {msg}")
        return "\n".join(lines)


def load_json(path: Path, problems: Problems) -> dict | None:
    try:
        raw = path.read_bytes()
    except OSError as e:
        problems.add(f"could not read file: {e}")
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.add(f"file is not UTF-8: {e}")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        problems.add(f"file is not valid JSON: {e.msg} (line {e.lineno}, col {e.colno})")
        return None


def check_top_level(doc: dict, problems: Problems) -> tuple[dict | None, list | None]:
    if not isinstance(doc, dict):
        problems.add("top level is not a JSON object")
        return None, None
    if "@context" not in doc:
        problems.add("missing top-level '@context'")
    if "@graph" not in doc:
        problems.add("missing top-level '@graph'")
    surprising = set(doc) - {"@context", "@graph"}
    if surprising:
        problems.add(
            f"unexpected top-level keys (only @context and @graph are expected): "
            f"{sorted(surprising)}"
        )
    ctx = doc.get("@context") if isinstance(doc.get("@context"), dict) else None
    graph = doc.get("@graph") if isinstance(doc.get("@graph"), list) else None
    if doc.get("@context") is not None and ctx is None:
        problems.add("'@context' must be a JSON object")
    if doc.get("@graph") is not None and graph is None:
        problems.add("'@graph' must be a JSON array")
    return ctx, graph


def detect_custom_prefix(ctx: dict, problems: Problems) -> str | None:
    """The custom prefix is whichever key maps to an IRI that isn't schema.org."""
    candidates = []
    for k, v in ctx.items():
        if k.startswith("@"):
            continue
        if isinstance(v, str) and v.startswith(("http://", "https://")) and "schema.org" not in v:
            candidates.append(k)
    if not candidates:
        problems.add(
            "no custom namespace prefix found in @context — expected something like "
            "\"sro\": \"http://example.org/sro#\" alongside the schema.org entry"
        )
        return None
    if len(candidates) > 1:
        problems.add(
            f"multiple custom namespace prefixes found {candidates}; the convention is "
            f"exactly one custom prefix plus 'schema'"
        )
    return candidates[0]


def check_context(ctx: dict, problems: Problems) -> str | None:
    if ctx is None:
        return None

    # Two-namespace pattern.
    has_schema_org = any(
        isinstance(v, str) and "schema.org" in v for v in ctx.values()
    )
    if not has_schema_org:
        problems.add(
            "@context does not reference schema.org — the Context Studio convention is "
            "to use schema.org as the base vocabulary"
        )

    custom_prefix = detect_custom_prefix(ctx, problems)

    # id / type shortcuts.
    if ctx.get("id") != "@id":
        problems.add('@context must include "id": "@id" so members of @graph can use '
                     '"id" instead of "@id"')
    if ctx.get("type") != "@type":
        problems.add('@context must include "type": "@type" so members of @graph can use '
                     '"type" instead of "@type"')

    # Type aliases.
    for type_name in VALID_TYPES:
        if type_name not in ctx:
            problems.add(
                f"@context missing the '{type_name}' alias — add "
                f'"{type_name}": "<prefix>:{type_name}"'
            )

    # IRI-reference fields must be declared with "@type": "@id".
    for field in IRI_REFERENCE_FIELDS:
        if field not in ctx:
            # Missing entirely — fine if the schema doesn't use it. We'll catch
            # usages of undeclared fields later when scanning @graph.
            continue
        entry = ctx[field]
        if isinstance(entry, str):
            problems.add(
                f"@context '{field}' is declared as a plain string mapping; it should be "
                f'an object {{"@id": "<prefix>:{field}", "@type": "@id"}} so values are '
                f"treated as references to other @graph members (this is the most common "
                f"cause of 'graph looks empty after import')"
            )
        elif isinstance(entry, dict):
            if entry.get("@type") != "@id":
                problems.add(
                    f"@context '{field}' is missing '\"@type\": \"@id\"'; without it, "
                    f"values won't be treated as references to other @graph members"
                )

    return custom_prefix


def check_graph(graph: list, custom_prefix: str | None, problems: Problems) -> None:
    if graph is None:
        return
    if not graph:
        problems.add("@graph is empty")
        return

    seen_ids: dict[str, int] = {}
    for i, member in enumerate(graph):
        if not isinstance(member, dict):
            problems.add(f"@graph[{i}] is not a JSON object")
            continue

        # Required fields.
        for required in ("id", "type", "name"):
            if required not in member:
                problems.add(f"@graph[{i}] is missing required field '{required}'")

        member_id = member.get("id")
        member_type = member.get("type")
        member_name = member.get("name") or f"<index {i}>"

        # id uniqueness.
        if isinstance(member_id, str):
            if member_id in seen_ids:
                problems.add(
                    f"duplicate id '{member_id}' (first seen at @graph[{seen_ids[member_id]}], "
                    f"again at @graph[{i}])"
                )
            else:
                seen_ids[member_id] = i

        # type must be one of the three.
        if member_type is not None and member_type not in VALID_TYPES:
            problems.add(
                f"@graph[{i}] '{member_name}' has type '{member_type}'; expected one of "
                f"{sorted(VALID_TYPES)}"
            )

        # Operation needs from / to.
        if member_type == "Operation":
            for required in ("from", "to"):
                if required not in member:
                    problems.add(
                        f"@graph[{i}] '{member_name}' is an Operation but is missing "
                        f"'{required}'"
                    )

        # id should use the declared prefix.
        if custom_prefix and isinstance(member_id, str):
            if ":" not in member_id:
                problems.add(
                    f"@graph[{i}] '{member_name}' has id '{member_id}' which is missing "
                    f"a namespace prefix (expected '{custom_prefix}:...')"
                )
            else:
                used_prefix = member_id.split(":", 1)[0]
                if used_prefix != custom_prefix:
                    problems.add(
                        f"@graph[{i}] '{member_name}' has id '{member_id}' using prefix "
                        f"'{used_prefix}' but the declared custom prefix is '{custom_prefix}'"
                    )

    # Cross-references resolve.
    for i, member in enumerate(graph):
        if not isinstance(member, dict):
            continue
        member_name = member.get("name") or f"<index {i}>"
        for field in CROSS_REF_FIELDS:
            if field not in member:
                continue
            value = member[field]
            refs = value if isinstance(value, list) else [value]
            for ref in refs:
                if not isinstance(ref, str):
                    problems.add(
                        f"@graph[{i}] '{member_name}'.{field} contains a non-string value: "
                        f"{ref!r}"
                    )
                    continue
                if ref not in seen_ids:
                    problems.add(
                        f"@graph[{i}] '{member_name}'.{field} references '{ref}' which is "
                        f"not a member of @graph (dangling reference)"
                    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a JSON-LD ontology against the Context Studio conventions."
    )
    parser.add_argument("path", type=Path, help="Path to the .jsonld file to validate.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the 'OK' message; only print on failure.",
    )
    args = parser.parse_args()

    problems = Problems()

    doc = load_json(args.path, problems)
    if doc is not None:
        ctx, graph = check_top_level(doc, problems)
        custom_prefix = check_context(ctx, problems) if ctx is not None else None
        if graph is not None:
            check_graph(graph, custom_prefix, problems)

    if problems:
        print(problems.report(), file=sys.stderr)
        return 1
    if not args.quiet:
        print(problems.report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
