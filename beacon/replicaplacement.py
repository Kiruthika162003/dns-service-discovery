"""Replica placement: spread a key's copies across failure domains, doubling only when forced.

Storing several copies of a key is pointless for durability if the
copies share a fate, so replica placement must spread them across
failure domains, different racks or zones, so that losing one domain
loses at most one copy. The placement walks the nodes in the order a
rendezvous score ranks them, which gives the key a stable preference
and minimal movement, but instead of taking the top few outright it
takes the highest-ranked node in each distinct domain first, so the
copies land in as many different domains as there are, and only if
the replica count exceeds the number of domains does it come back and
double up, taking a second node in an already-used domain. That
best-effort diversity is honest about its limit: three copies across
two zones can only ever put two in one zone, so losing that zone
loses two of the three, and no placement can do better with two
zones, which is a fact about the topology, not a flaw in the
algorithm. The module ranks the nodes, fills distinct domains first,
then fills the remainder ignoring domain, and reports how many
distinct domains the placement achieved, so the diversity is a
measured property and its bound is visible.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _score(key: str, node: str) -> int:
    digest = hashlib.blake2b(
        f"{node}\x00{key}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big")


def place(
    key: str, nodes: dict[str, str], replicas: int
) -> list[str]:
    if replicas < 1:
        raise Invalid("a placement of zero replicas stores nothing")
    if replicas > len(nodes):
        raise Invalid(
            f"{replicas} replicas asked of {len(nodes)} nodes; a "
            "key cannot have more copies than there are nodes"
        )
    ranked = sorted(nodes, key=lambda n: _score(key, n), reverse=True)
    chosen: list[str] = []
    used_domains: set[str] = set()
    for node in ranked:
        if len(chosen) >= replicas:
            break
        if nodes[node] not in used_domains:
            chosen.append(node)
            used_domains.add(nodes[node])
    for node in ranked:
        if len(chosen) >= replicas:
            break
        if node not in chosen:
            chosen.append(node)
    return chosen


def domains_covered(placement: list[str], nodes: dict[str, str]) -> int:
    return len({nodes[node] for node in placement})
