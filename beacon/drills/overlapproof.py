"""The quorum overlap rule, proven by exhaustion rather than asserted.

The claim that R plus W greater than N gives strong
consistency is the kind of rule people memorize and misapply,
so this drill proves it the only honest way: enumerate every
read set and write set of the stated sizes over N replicas,
and check whether every read set intersects every write set.
For a configuration the formula calls consistent, the drill
confirms zero disjoint read-write pairs exist; for one the
formula calls inconsistent, it confirms at least one disjoint
pair does, the exact pair where a read can miss the write.
The measurement is the point: the formula and the exhaustive
truth agree on both a 3-2-2 config that overlaps always and a
5-2-2 config that has 30 disjoint pairs, so the rule is not
taken on faith but watched holding across every combination
it governs.
"""

from __future__ import annotations

from itertools import combinations

from beacon.drills.finding import Finding
from beacon.quorumreads import QuorumConfig


def _disjoint_pairs(replicas: int, r: int, w: int) -> int:
    nodes = range(replicas)
    disjoint = 0
    for read_set in combinations(nodes, r):
        for write_set in combinations(nodes, w):
            if not set(read_set) & set(write_set):
                disjoint += 1
    return disjoint


def run() -> Finding:
    consistent = QuorumConfig(
        replicas=3, read_quorum=2, write_quorum=2
    )
    inconsistent = QuorumConfig(
        replicas=5, read_quorum=2, write_quorum=2
    )
    consistent_disjoint = _disjoint_pairs(3, 2, 2)
    inconsistent_disjoint = _disjoint_pairs(5, 2, 2)
    numbers = {
        "consistent_formula": consistent.strongly_consistent(),
        "consistent_disjoint_pairs": consistent_disjoint,
        "inconsistent_formula": (
            inconsistent.strongly_consistent()
        ),
        "inconsistent_disjoint_pairs": inconsistent_disjoint,
    }
    holds = (
        numbers["consistent_formula"]
        and numbers["consistent_disjoint_pairs"] == 0
        and not numbers["inconsistent_formula"]
        and numbers["inconsistent_disjoint_pairs"] == 30
    )
    return Finding(
        drill="overlapproof",
        claim=(
            "the R+W>N rule holds by exhaustion: the 3-2-2 "
            "config has zero disjoint read-write pairs and the "
            "5-2-2 config has thirty, matching the formula on "
            "every combination it governs"
        ),
        numbers=numbers,
        holds=holds,
    )
