"""Rendezvous hashing: every key ranks every node, and a lost node moves only its own.

Consistent hashing places nodes on a ring and walks clockwise,
which works but needs virtual nodes to spread load evenly and
still wobbles when the ring is small. Rendezvous hashing, also
called highest random weight, takes a different route to the
same guarantee: for a given key it scores every node with a hash
of the pair and picks the highest, so the mapping is a total
ranking of nodes per key rather than a position on a circle. The
property that matters for service discovery is minimal
disruption. When a node is removed, only the keys that ranked it
first move, and each of those moves to its own second choice,
never disturbing a key that preferred a surviving node, so
removing one of N nodes reshuffles about one part in N of the
keys and no more. The module measures that fraction directly,
because the promise of minimal disruption is only worth stating
if it can be counted, and a rebalancing that moved far more than
its share would be a bug wearing the algorithm's name.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _score(key: str, node: str) -> int:
    digest = hashlib.blake2b(
        f"{node}\x00{key}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big")


def choose(key: str, nodes: list[str]) -> str:
    if not nodes:
        raise Invalid(
            "rendezvous hashing needs at least one node; an "
            "empty pool ranks nothing"
        )
    return max(nodes, key=lambda node: _score(key, node))


def ranking(key: str, nodes: list[str]) -> list[str]:
    return sorted(
        nodes, key=lambda node: _score(key, node), reverse=True
    )


def disruption(
    keys: list[str], nodes: list[str], removed: str
) -> float:
    if removed not in nodes:
        raise Invalid(
            f"{removed} is not in the pool, so removing it "
            "disrupts nothing and the question is ill-posed"
        )
    survivors = [node for node in nodes if node != removed]
    if not survivors:
        raise Invalid(
            "removing the last node leaves nowhere to move the "
            "keys; that is an outage, not a rebalancing"
        )
    moved = 0
    for key in keys:
        before = choose(key, nodes)
        after = choose(key, survivors)
        if before != after:
            moved += 1
    return moved / len(keys)
