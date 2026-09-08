"""Capacity planning for N+k: run enough spare that k simultaneous failures do not overload.

A cluster sized to exactly carry its load has no margin, so the first
node to fail hands its share to the survivors, pushing them over
capacity, and their overload fails them in turn, a cascade from a
single failure. Provisioning for N+k means running enough nodes that
even after k of them fail, the remaining nodes can still carry the
whole load without exceeding their capacity. The arithmetic is
simple, the surviving nodes times their per-node capacity must be at
least the load, and the module turns it into the questions an
operator actually asks: does this cluster survive k failures, how
many simultaneous failures can it tolerate before the survivors are
overloaded, and how much headroom is left after k fail. The honest
cost is that the spare capacity sits idle in the common case when
nothing has failed, which is money spent on a margin that earns
nothing until the day it is the difference between a shrug and an
outage, so N+k is a deliberate purchase of resilience, not free
prudence, and underprovisioning saves that money right up until k
nodes fail together. The module computes survival, the maximum
tolerable failures, and the post-failure headroom, so the margin is
a number rather than a hope.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _validate(nodes: int, capacity_per_node: float, load: float) -> None:
    if nodes < 1:
        raise Invalid("a cluster needs at least one node")
    if capacity_per_node <= 0:
        raise Invalid("a node's capacity must be positive")
    if load < 0:
        raise Invalid("load is never negative")


def survives_failures(
    nodes: int, capacity_per_node: float, load: float, k: int
) -> bool:
    _validate(nodes, capacity_per_node, load)
    surviving = nodes - k
    if surviving < 1:
        return False
    return surviving * capacity_per_node >= load


def max_tolerable_failures(
    nodes: int, capacity_per_node: float, load: float
) -> int:
    _validate(nodes, capacity_per_node, load)
    tolerated = 0
    while survives_failures(nodes, capacity_per_node, load, tolerated + 1):
        tolerated += 1
    return tolerated


def headroom(
    nodes: int, capacity_per_node: float, load: float, k: int
) -> float:
    _validate(nodes, capacity_per_node, load)
    return (nodes - k) * capacity_per_node - load
