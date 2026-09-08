"""Levenshtein distance: how many single-character edits separate two strings.

The edit distance between two strings is the fewest single-character
insertions, deletions, or substitutions that turn one into the other,
and it is the foundation of typo detection and fuzzy matching, a
mistyped name is close in edit distance to the one intended. It is
computed by dynamic programming over a grid whose cell holds the
distance between prefixes of the two strings, each cell one more than
the best of its three neighbors unless the characters match, and the
bottom-right corner is the answer. The cost is the product of the two
lengths, quadratic, which is fine for comparing two strings but too
slow to scan a large dictionary one entry at a time, so large-scale
fuzzy matching builds an index, a BK-tree or an n-gram index, on top
of the distance rather than computing it against every candidate. A
common need is only to know whether the distance is within a small
bound, which the module also answers, and though it computes the full
distance here, that bounded question is what permits the early
termination a production matcher uses. The module computes the edit
distance with the row-by-row dynamic program and decides whether two
strings are within a given edit bound.
"""

from __future__ import annotations

from beacon.errors import Invalid


def distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def within(a: str, b: str, bound: int) -> bool:
    if bound < 0:
        raise Invalid("an edit bound is never negative")
    return distance(a, b) <= bound
