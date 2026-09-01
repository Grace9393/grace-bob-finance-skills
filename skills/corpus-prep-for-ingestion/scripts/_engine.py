# -*- coding: utf-8 -*-
"""Locate the shared deep-extract engine.

One implementation of container parsing is maintained, in the `deep-extract`
skill. Skills that need to read a document import it through this shim rather
than carrying their own parser, so a fix lands everywhere at once.

Copy this file into any skill that needs the engine; it searches, in order:
  1. the calling skill's own scripts/ directory (a vendored copy, if any)
  2. sibling skill directories in the same skills root, under either the
     numbered layout (`13-deep-extract`) or the installed layout (`deep-extract`)
  3. the usual Claude / Bob install roots
"""

import importlib.util
import os

MIN_VERSION = (1, 1, 0)

_here = os.path.dirname(os.path.abspath(__file__))
_skill = os.path.dirname(_here)              # …/<skill>
_root = os.path.dirname(_skill)              # …/<skills root>

_CANDIDATES = [
    _here,
    os.path.join(_root, "deep-extract", "scripts"),
    os.path.join(_root, "13-deep-extract", "scripts"),
    os.path.expanduser(os.path.join("~", ".claude", "skills", "deep-extract",
                                    "scripts")),
    os.path.expanduser(os.path.join("~", ".bob", "skills", "deep-extract",
                                    "scripts")),
]


class EngineMissing(RuntimeError):
    pass


def _parse_version(v):
    try:
        return tuple(int(x) for x in str(v).split(".")[:3])
    except Exception:
        return (0, 0, 0)


def load(required=True):
    """Import and return the deep_extract module, or None when optional."""
    tried = []
    for cand in _CANDIDATES:
        path = os.path.abspath(os.path.join(cand, "deep_extract.py"))
        tried.append(path)
        if not os.path.isfile(path):
            continue
        spec = importlib.util.spec_from_file_location("deep_extract", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        have = _parse_version(getattr(mod, "__version__", "0"))
        if have < MIN_VERSION:
            raise EngineMissing(
                "deep_extract at %s is version %s; %s or newer is required. "
                "Update the deep-extract skill."
                % (path, ".".join(map(str, have)),
                   ".".join(map(str, MIN_VERSION))))
        return mod
    if not required:
        return None
    raise EngineMissing(
        "This skill needs the shared extraction engine from the `deep-extract` "
        "skill, which was not found. Install deep-extract alongside this skill "
        "(same skills directory). Looked in:\n  " + "\n  ".join(tried))
