"""Weighted rendezvous hashing: minimal-disruption placement that also honors uneven capacities.

Plain rendezvous hashing spreads keys evenly and moves only a key's
own share when a node leaves, but it assumes every node is equal,
which real fleets are not: a large backend should hold more keys
than a small one. Weighted rendezvous hashing keeps the minimal-
disruption property while making a node's share proportional to a
weight. It scores a node for a key not by a bare hash but by a hash
transformed so that a heavier weight raises the score in exactly the
proportion that makes selection frequency track the weight, and it
still picks the highest-scoring node, so a key moves only when the
node it preferred changes, the same locality guarantee. The
transform matters: dividing the weight by the negative log of a
uniform hash gives each node a selection probability proportional to
its weight, a result from the theory of weighted sampling, so
doubling a node's weight doubles its expected keys without disturbing
how the rest are distributed. The module scores, chooses, ranks, and
measures the realized distribution against the weights and the
disruption when a node is removed, so both the proportional loading
and the minimal movement are numbers rather than claims.
"""

from __future__ import annotations

import hashlib
import math

from beacon.errors import Invalid


def _unit(key: str, node: str) -> float:
    digest = hashlib.blake2b(
        f"{node}\x00{key}".encode(), digest_size=8
    ).digest()
    raw = int.from_bytes(digest, "big")
    return (raw + 1) / (2**64 + 1)


def _score(key: str, node: str, weight: float) -> float:
    if weight <= 0:
        raise Invalid(
            f"node {node} has weight {weight}; a node in the pool "
            "must have a positive weight or it holds no keys"
        )
    return weight / -math.log(_unit(key, node))


def choose(key: str, nodes: dict[str, float]) -> str:
    if not nodes:
        raise Invalid("an empty pool ranks no node for the key")
    return max(nodes, key=lambda node: _score(key, node, nodes[node]))


def ranking(key: str, nodes: dict[str, float]) -> list[str]:
    return sorted(
        nodes,
        key=lambda node: _score(key, node, nodes[node]),
        reverse=True,
    )


def distribution(
    keys: list[str], nodes: dict[str, float]
) -> dict[str, int]:
    counts = dict.fromkeys(nodes, 0)
    for key in keys:
        counts[choose(key, nodes)] += 1
    return counts


def disruption(
    keys: list[str], nodes: dict[str, float], removed: str
) -> float:
    if removed not in nodes:
        raise Invalid(f"{removed} is not in the pool to remove")
    survivors = {n: w for n, w in nodes.items() if n != removed}
    if not survivors:
        raise Invalid("removing the last node is an outage, not a rebalance")
    moved = sum(
        1
        for key in keys
        if choose(key, nodes) != choose(key, survivors)
    )
    return moved / len(keys)
