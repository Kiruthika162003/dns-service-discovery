"""Merkle divergence costs a logarithm, not a scan, and the drill counts the difference.

The reason to build a Merkle tree at all is that finding a single
diverged key between two large replicas should cost the depth of
the tree, not its width, and that saving is a claim a build can
silently lose. The drill takes a 1024-key dataset, changes exactly
one value on the second replica, and asserts both that the one
diverged key is the one found and that the descent touched fewer
than thirty nodes, a handful against a thousand. It also holds the
cheap case, that identical replicas settle on a single root
comparison, because the common case in anti-entropy is agreement
and it must cost almost nothing. Together the two numbers are the
whole argument for the tree: agreement is one comparison,
divergence is logarithmic, and neither is linear in the dataset.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.merkletree import MerkleTree, divergent_keys

BASE = {f"k{i:04d}": f"v{i}" for i in range(1024)}


def run() -> Finding:
    other = dict(BASE)
    other["k0500"] = "changed"
    found, comparisons = divergent_keys(
        MerkleTree(BASE), MerkleTree(other)
    )
    _, agree_cost = divergent_keys(
        MerkleTree(BASE), MerkleTree(dict(BASE))
    )
    numbers = {
        "keys": len(BASE),
        "found": found,
        "comparisons": comparisons,
        "agreement_cost": agree_cost,
        "logarithmic": comparisons < 30,
    }
    holds = (
        found == ["k0500"]
        and comparisons < 30
        and agree_cost == 1
    )
    return Finding(
        drill="merkle",
        claim=(
            "one diverged key in 1024 is found in under 30 node "
            "comparisons, and identical replicas agree in a single "
            "root comparison, so agreement is O(1) and divergence "
            "is logarithmic, never linear in the dataset"
        ),
        numbers=numbers,
        holds=holds,
    )
