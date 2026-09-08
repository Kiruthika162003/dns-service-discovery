"""Bellman-Ford: shortest paths that tolerate negative edges and expose bad cycles.

Dijkstra's algorithm is faster but assumes every edge weight is
non-negative, and that assumption breaks the moment weights can model
something like a rebate, a gain, or a currency conversion that can move
either way. Bellman-Ford drops the assumption. It relaxes every edge
repeatedly, and because any shortest path in a graph of n vertices uses
at most n minus one edges, n minus one full passes are enough for the
distances to settle. The cost is that bluntness: it does the work of a
full sweep each pass rather than following a frontier, so it is slower
than Dijkstra where both apply. Its real prize is the extra pass. If any
edge can still be relaxed after the distances should have converged,
that edge lies on or downstream of a negative-weight cycle, a loop you
could traverse forever to drive the cost to minus infinity, and no
shortest path is well defined. This module returns the distances from a
source, or reports that a negative cycle is reachable rather than
returning numbers that a negative cycle has made meaningless. It refuses
a source outside the vertex range and an edge that names a vertex that
does not exist.
"""

from __future__ import annotations

from beacon.errors import Invalid

Edge = tuple[int, int, float]


def shortest_paths(
    vertex_count: int, edges: list[Edge], source: int
) -> list[float] | None:
    if vertex_count <= 0:
        raise Invalid(
            f"the graph has {vertex_count} vertices; it must have at least one"
        )
    if not 0 <= source < vertex_count:
        raise Invalid(
            f"the source {source} is outside the range 0 to {vertex_count - 1}"
        )
    for tail, head, _ in edges:
        if not 0 <= tail < vertex_count or not 0 <= head < vertex_count:
            raise Invalid(
                f"edge ({tail}, {head}) names a vertex outside the range 0 to "
                f"{vertex_count - 1}"
            )
    distance = [float("inf")] * vertex_count
    distance[source] = 0.0
    for _ in range(vertex_count - 1):
        changed = False
        for tail, head, weight in edges:
            if distance[tail] + weight < distance[head]:
                distance[head] = distance[tail] + weight
                changed = True
        if not changed:
            break
    for tail, head, weight in edges:
        if distance[tail] + weight < distance[head]:
            return None
    return distance
