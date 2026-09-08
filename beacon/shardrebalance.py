"""Shard rebalancing: level the load across nodes while moving as few shards as possible.

When a node is added to or removed from a sharded store, the shards
must be rebalanced, and the cost that dominates is data movement,
since relocating a shard means copying its data across the network,
so a good rebalance moves the fewest shards that still levels the
load. The naive rebalance, rehashing every shard onto the new node
set, is correct and catastrophic, because it can move nearly every
shard when only a fraction needed to. The minimal-movement rebalance
keeps each shard where it is whenever its current node still exists
and is not yet over the target load, and it moves only the shards
that are orphaned by a removed node or that spill over a node past
the even target. The target is the total shard count divided across
the surviving nodes, rounded up, so no node exceeds it, and the
shards that must move go to the nodes under the target. The result
levels the load while touching only the necessary shards, about one
node's worth on an add, which is the same minimal-disruption goal a
consistent hash pursues, made explicit here as a count of moves. The
module computes the new assignment and the number of shards it moved,
so the movement is a measured cost rather than a hidden one.
"""

from __future__ import annotations

from math import ceil

from beacon.errors import Invalid


def rebalance(
    assignment: dict[str, str], nodes: list[str]
) -> tuple[dict[str, str], int]:
    if not nodes:
        raise Invalid("no nodes to rebalance shards onto")
    if not assignment:
        return {}, 0
    target = ceil(len(assignment) / len(nodes))
    counts = dict.fromkeys(nodes, 0)
    result: dict[str, str] = {}
    orphans: list[str] = []
    for shard, node in assignment.items():
        if node in counts and counts[node] < target:
            result[shard] = node
            counts[node] += 1
        else:
            orphans.append(shard)
    for shard in orphans:
        node = min(nodes, key=lambda n: (counts[n], n))
        result[shard] = node
        counts[node] += 1
    moves = sum(
        1 for shard in assignment if result[shard] != assignment[shard]
    )
    return result, moves
