"""Scuttlebutt reconciliation: trade version digests, then send only the deltas a peer lacks.

Gossiping full state every round wastes bandwidth once a cluster
is mostly converged, since the vast majority of what a node holds,
its peer already has. Scuttlebutt reconciliation, the style Cassandra
uses, sends a cheap digest first, just a version number per key, and
lets each side compute exactly what the other is missing. A node
comparing its own state against a peer's digest finds the keys where
its version is higher and sends those as deltas, and finds the keys
where the peer's version is higher and asks for them, so each round
moves only the differences rather than the whole state. When there
is more to send than one round's budget allows, the deltas are
ordered by how far behind they are, the largest version gap first,
so the most out-of-date information converges soonest and a node
rejoining after a long absence catches up on what changed most
rather than on whatever happened to sort first. The module computes
the deltas a peer needs from a digest, the keys the local node
should request, and orders a send by version gap under a budget, so
reconciliation moves the difference, newest gaps first.
"""

from __future__ import annotations

from beacon.errors import Invalid


def deltas_for_peer(
    mine: dict[str, tuple[str, int]],
    peer_digest: dict[str, int],
) -> dict[str, tuple[str, int]]:
    return {
        key: (value, version)
        for key, (value, version) in mine.items()
        if version > peer_digest.get(key, 0)
    }


def keys_i_need(
    my_digest: dict[str, int], peer_digest: dict[str, int]
) -> list[str]:
    return sorted(
        key
        for key, version in peer_digest.items()
        if version > my_digest.get(key, 0)
    )


def prioritize(
    deltas: dict[str, tuple[str, int]],
    peer_digest: dict[str, int],
    budget: int,
) -> list[str]:
    if budget < 0:
        raise Invalid("a send budget is never negative")
    gaps = [
        (key, version - peer_digest.get(key, 0))
        for key, (_, version) in deltas.items()
    ]
    gaps.sort(key=lambda item: (-item[1], item[0]))
    return [key for key, _ in gaps[:budget]]
