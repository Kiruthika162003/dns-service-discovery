"""Merkle anti-entropy: find the diverged key without reading both replicas whole.

Two replicas of a registry drift, a write landed on one and not
the other, and reconciling them by shipping and comparing every
key would cost bandwidth proportional to the whole dataset to
find a difference that might be a single record. A Merkle tree
turns that linear scan into a logarithmic descent. Each replica
hashes its key-value pairs into the leaves of a binary tree and
combines child hashes up to a single root, and to compare, the
replicas exchange roots: if the roots match the datasets are
identical and nothing more is sent, and if they differ each side
descends only into the child whose hash disagrees, halving the
search at every step until it reaches the diverged leaves. The
saving is the entire point and the module measures it, counting
the nodes compared so a divergence of one key in a thousand is
shown to cost a handful of comparisons rather than a thousand,
and it refuses to compare trees over different key sets, since
this form finds diverged values, not added or removed keys.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


class MerkleTree:
    def __init__(self, items: dict[str, str]) -> None:
        self.items = dict(items)
        self.keys = sorted(items)
        self._memo: dict[tuple[int, int], str] = {}

    def _leaf(self, key: str) -> str:
        return hashlib.blake2b(
            f"{key}={self.items[key]}".encode(), digest_size=8
        ).hexdigest()

    def node_hash(self, lo: int, hi: int) -> str:
        cached = self._memo.get((lo, hi))
        if cached is not None:
            return cached
        if hi - lo == 1:
            result = self._leaf(self.keys[lo])
        else:
            mid = (lo + hi) // 2
            combined = self.node_hash(lo, mid) + self.node_hash(mid, hi)
            result = hashlib.blake2b(
                combined.encode(), digest_size=8
            ).hexdigest()
        self._memo[(lo, hi)] = result
        return result

    def root(self) -> str:
        if not self.keys:
            return ""
        return self.node_hash(0, len(self.keys))


def divergent_keys(
    left: MerkleTree, right: MerkleTree
) -> tuple[list[str], int]:
    if left.keys != right.keys:
        raise Invalid(
            "the two trees cover different key sets; this "
            "comparison finds diverged values, not added or "
            "removed keys, so equal key sets are required"
        )
    found: list[str] = []
    comparisons = 0

    def descend(lo: int, hi: int) -> None:
        nonlocal comparisons
        comparisons += 1
        if left.node_hash(lo, hi) == right.node_hash(lo, hi):
            return
        if hi - lo == 1:
            found.append(left.keys[lo])
            return
        mid = (lo + hi) // 2
        descend(lo, mid)
        descend(mid, hi)

    if left.keys:
        descend(0, len(left.keys))
    return sorted(found), comparisons
