#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_vocabulary.py - is any word on this page foreign to the corpus?

`audit_page_tokens.py` checks the numbers, codes and dates. `audit_source_coverage.py`
checks nothing was dropped. Neither catches the failure that matters most when a
client says "only from these documents": a *prose* claim that reads plausibly
and is not in any of them.

A curated claim list is the usual answer and it drifts. This needs no list. A
synthesis may invent structure, transitions and argument - it may not invent
subject matter, and subject matter shows up as vocabulary. So: take every content
word and noun phrase on the printed page, and report the ones that appear in none
of the sources. Whatever comes back is either the page's own connective language,
which is fine, or an imported fact, which is not. A human reads the residual;
the script only has to make it short enough to read.

    python audit_vocabulary.py PAGE.html --source D1=a.html --source D2=b.html
    python audit_vocabulary.py PAGE.html --source-dir ./sources --include-screen

Prints two lists: single words absent from every source, and two-word phrases
absent from every source. The second matters more - "accounts" and "payable" can
both be in the corpus while "accounts payable" is a subject nobody wrote about.
That exact recombination once put an Accounts Payable framing on an Accounts
Receivable engagement.

Exit codes: 0 the residual is empty, 1 there is something to read. A non-zero
exit here is a prompt to look, not proof of a defect.
"""

from __future__ import annotations

import argparse
import glob
import html as H
import io
import os
import re
import sys

# Function words, and the connective vocabulary a synthesis is entitled to use.
# Deliberately small: anything domain-bearing must NOT be here, or the audit
# starts excusing exactly what it exists to catch.
STOP = set("""
a an the and or but nor so yet for if then than that this these those there here
is are was were be been being am do does did done doing have has had having
can could will would shall should may might must ought
i you he she it we they them him her his hers its our ours your yours their theirs
of in on at by to from with without into onto over under above below between among
across through during before after since until while about against within upon
not no none never always all any both each few more most other some such only own
same very just also too as at once again further once
what which who whom whose when where why how
one two three four five six seven eight nine ten eleven twelve twenty thirty
first second third fourth fifth last next
page report reports document documents section sections note notes
say says said state states stated show shows shown give gives given
make makes made take takes taken put puts run runs ran go goes went come comes
get gets got keep keeps kept leave leaves left find finds found
because therefore however although though whereas rather instead yet still
means meaning matter matters point points thing things way ways part parts
""".split())

WORD = re.compile(r"[A-Za-z][A-Za-z'&/.-]*[A-Za-z]|[A-Za-z]")


def plain(path):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"<style.*?</style>|<script.*?</script>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).lower()


def printed_text(path, include_screen):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(io.open(path, encoding="utf-8", errors="replace").read(), "lxml")
    for t in soup.select("style, script"):
        t.decompose()
    if not include_screen:
        for t in soup.select(".screen-only, .topnav, .totop"):
            t.decompose()
    # newline between elements so a phrase cannot be manufactured out of two
    # neighbouring blocks that happen to sit side by side
    return "\n".join(s for s in soup.stripped_strings)


def normalise(w):
    """Crude de-inflection. Better to over-match the corpus than to raise a
    flag on a plural - a false alarm costs a human read of the source."""
    w = w.strip("'.-&/").lower()
    for suffix in ("'s", "s'", "ing", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suffix):
            yield w[:len(w) - len(suffix)]
    yield w


def in_corpus(word, corpus):
    return any(v and v in corpus for v in normalise(word))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Report page vocabulary absent from every source.")
    ap.add_argument("page")
    ap.add_argument("--source", action="append", default=[], metavar="CODE=PATH")
    ap.add_argument("--source-dir")
    ap.add_argument("--include-screen", action="store_true",
                    help="also audit the screen-only layer (default: printed sheet only)")
    ap.add_argument("--allow", default="", help="comma-separated words that are ours by design")
    args = ap.parse_args(argv)

    paths = []
    for pair in args.source:
        _, _, p = pair.partition("=")
        paths.append(p)
    if args.source_dir:
        paths += [p for p in sorted(glob.glob(os.path.join(args.source_dir, "*")))
                  if os.path.splitext(p)[1].lower() in (".html", ".htm", ".md", ".txt")]
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing or not paths:
        print("FAIL  source not found: %s" % (", ".join(missing) or "none given"))
        return 2

    corpus = " ".join(plain(p) for p in paths)
    allow = {w.strip().lower() for w in args.allow.split(",") if w.strip()}
    text = printed_text(args.page, args.include_screen)

    lone, seen = [], set()
    for line in text.split("\n"):
        for w in WORD.findall(line):
            key = w.lower()
            if key in STOP or key in allow or len(key) < 3 or key in seen:
                continue
            seen.add(key)
            if not in_corpus(w, corpus):
                lone.append(w)

    phrases, pseen = [], set()
    for line in text.split("\n"):
        words = [w for w in WORD.findall(line)]
        for a, b in zip(words, words[1:]):
            if a.lower() in STOP or b.lower() in STOP:
                continue
            phrase = "%s %s" % (a, b)
            if phrase.lower() in pseen or phrase.lower() in allow:
                continue
            pseen.add(phrase.lower())
            if phrase.lower() not in corpus:
                # both halves known, the pairing not - the interesting case
                if in_corpus(a, corpus) and in_corpus(b, corpus):
                    phrases.append(phrase)

    scope = "whole page" if args.include_screen else "printed sheet only"
    print("audited: %s   sources: %d\n" % (scope, len(paths)))
    print("WORDS ON THE PAGE THAT APPEAR IN NO SOURCE  (%d)" % len(lone))
    print("-" * 62)
    # capitalised or digit-bearing first: those are the ones that carry subject
    for w in sorted(lone, key=lambda s: (not (s[0].isupper() or any(c.isdigit() for c in s)),
                                         s.lower())):
        print("   %s%s" % (w, "   <-- proper noun or figure" if s_flag(w) else ""))
    print()
    print("TWO-WORD PHRASES ABSENT FROM EVERY SOURCE, BOTH HALVES PRESENT  (%d)" % len(phrases))
    print("-" * 62)
    print("   a synthesis recombines freely, so most of these are fine. Read them for")
    print("   the one that names a subject the corpus never discusses.\n")
    for p in sorted(set(phrases), key=str.lower):
        print("   %s" % p)
    print()
    print("  Neither list is a defect list. Read the residual: connective language is")
    print("  expected, an imported fact is not.")
    return 1 if (lone or phrases) else 0


def s_flag(w):
    return w[0].isupper() or any(c.isdigit() for c in w)


if __name__ == "__main__":
    sys.exit(main())
