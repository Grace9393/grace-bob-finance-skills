# -*- coding: utf-8 -*-
"""Find the extraction scripts this front-end dispatches to.

`extract` deliberately implements no parsing of its own. Each profile is served
by the script that already owns it, so there is still exactly one
implementation of each behaviour:

    deep      -> deep-extract/scripts/deep_extract.py
    contract  -> contract-review/scripts/contract_extract.py
    corpus    -> corpus-prep-for-ingestion/scripts/corpus_prep.py

Skill directories are searched under both the numbered source layout
(`13-deep-extract`) and the installed layout (`deep-extract`).
"""

import os

_here = os.path.dirname(os.path.abspath(__file__))
_skill = os.path.dirname(_here)
_root = os.path.dirname(_skill)

TARGETS = {
    "deep": (["deep-extract", "13-deep-extract"], "deep_extract.py"),
    "contract": (["contract-review", "07-contract-review"],
                 "contract_extract.py"),
    "corpus": (["corpus-prep-for-ingestion", "11-corpus-prep-for-ingestion"],
               "corpus_prep.py"),
}

SEARCH_ROOTS = [
    _root,
    os.path.expanduser(os.path.join("~", ".claude", "skills")),
    os.path.expanduser(os.path.join("~", ".bob", "skills")),
    os.path.join("H:" + os.sep, "My Drive", "AA", "bob-skills"),
    os.path.join("H:" + os.sep, "My Drive", "AA", ".bob", "skills"),
]


class Missing(RuntimeError):
    pass


def candidates(profile):
    dirs, script = TARGETS[profile]
    out = []
    for root in SEARCH_ROOTS:
        for d in dirs:
            out.append(os.path.join(root, d, "scripts", script))
    out.append(os.path.join(_here, script))          # vendored fallback
    return out


def find(profile, required=True):
    tried = candidates(profile)
    for p in tried:
        if os.path.isfile(p):
            return os.path.abspath(p)
    if not required:
        return None
    dirs, script = TARGETS[profile]
    raise Missing(
        "The `%s` profile needs `%s`, which ships with the `%s` skill. "
        "Install it in the same skills directory as `extract`.\nLooked in:\n  %s"
        % (profile, script, dirs[0], "\n  ".join(tried)))


def resolve_all():
    return {p: find(p, required=False) for p in TARGETS}
