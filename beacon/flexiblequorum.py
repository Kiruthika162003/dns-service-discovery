"""Flexible quorums: reads and writes need only overlap, not each be a majority.

Classic consensus used a majority for every quorum out of caution,
but flexible Paxos showed the caution was stronger than the
requirement. What correctness actually needs is that every quorum
used to elect a leader intersects every quorum used to replicate a
value, so that no value can be committed by one set and then lost to
a leader elected by a disjoint set. Intersection of two subsets of N
is guaranteed exactly when their sizes sum to more than N, and that
is the whole condition, Q1 plus Q2 greater than N, with no
requirement that either alone be a majority. This buys a real
tuning freedom. The common operation, replicating a value, can use a
small fast quorum if the rare operation, electing a leader, uses a
correspondingly large one, so a system that reads and writes far
more than it fails over can make the hot path cheap and pay for it
on the cold path. The module checks whether two quorum sizes
intersect over a cluster, computes the smallest replication quorum
that stays safe against a given election quorum, and refuses sizes
that do not fit the cluster, since a quorum larger than N is not a
subset of it.
"""

from __future__ import annotations

from beacon.errors import Invalid


def quorums_intersect(election_quorum: int, replication_quorum: int, n: int) -> bool:
    if not 1 <= election_quorum <= n or not 1 <= replication_quorum <= n:
        raise Invalid(
            f"a quorum must be between one and the {n} nodes; a "
            "quorum larger than the cluster is not a subset of it"
        )
    return election_quorum + replication_quorum > n


def min_replication_quorum(election_quorum: int, n: int) -> int:
    if not 1 <= election_quorum <= n:
        raise Invalid(
            f"the election quorum must be between one and {n}"
        )
    return n - election_quorum + 1
