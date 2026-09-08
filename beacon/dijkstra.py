"""Dijkstra's shortest paths: least-latency routes, valid because latencies are non-negative.

Routing a request across a mesh of services along the least-latency
path is a shortest-path problem, and Dijkstra's algorithm solves it
from a source when the edge weights, the latencies, are non-negative.
It keeps a frontier of nodes with tentative distances and repeatedly
finalizes the closest unfinalized node, because with non-negative
edges no later path can improve on the closest one already found, then
relaxes that node's edges, lowering its neighbors' tentative
distances where going through it is shorter. A min-heap over the
frontier makes selecting the closest cheap, giving near-linear-log
performance. The non-negativity is not a detail but the algorithm's
foundation: a negative edge could make a longer-looking path actually
shorter through a later discount, which Dijkstra would miss because
it finalizes a node before seeing that detour, so a graph with
negative weights needs Bellman-Ford instead. Latencies being always
non-negative is exactly why Dijkstra fits latency routing. The module
computes the shortest distance from a source to every reachable node
using a heap frontier, leaves unreachable nodes out, and refuses a
negative edge weight as outside what it can correctly solve.
"""

from __future__ import annotations

import heapq

from beacon.errors import Invalid


def shortest_paths(
    graph: dict[str, dict[str, int]], source: str
) -> dict[str, int]:
    for edges in graph.values():
        for weight in edges.values():
            if weight < 0:
                raise Invalid(
                    "a negative edge weight is outside what Dijkstra "
                    "solves correctly; use Bellman-Ford for those"
                )
    distances: dict[str, int] = {source: 0}
    frontier: list[tuple[int, str]] = [(0, source)]
    while frontier:
        dist, node = heapq.heappop(frontier)
        if dist > distances.get(node, float("inf")):
            continue
        for neighbor, weight in graph.get(node, {}).items():
            candidate = dist + weight
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heapq.heappush(frontier, (candidate, neighbor))
    return distances
