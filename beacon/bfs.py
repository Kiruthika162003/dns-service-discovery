"""Breadth-first search: fewest-hop distances and reachability over an unweighted graph.

When every edge costs the same, a hop, the shortest path is the one
with the fewest edges, and breadth-first search finds it by exploring
the graph in rings of increasing distance from the source. It visits
the source, then all its neighbors at distance one, then their
unvisited neighbors at distance two, and so on, so the first time it
reaches a node is by a fewest-hop path and the distance is fixed then
and there. A queue holds the frontier and a visited set stops it
revisiting, giving one linear pass over nodes and edges. This is the
unweighted special case of Dijkstra's algorithm, which BFS beats in
simplicity because with equal weights there is no need for a priority
queue, the plain queue already visits nodes in distance order.
Reachability falls out for free: the set of nodes BFS visits from a
source is exactly those reachable from it. The module computes the
hop distance from a source to every reachable node and the set of
reachable nodes, treating the adjacency map as given, so both the
fewest-hop metric and the reachability question are answered by the
one traversal.
"""

from __future__ import annotations

from collections import deque


def hop_distances(graph: dict[str, set[str]], source: str) -> dict[str, int]:
    distances = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, set()):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    return distances


def reachable(graph: dict[str, set[str]], source: str) -> set[str]:
    return set(hop_distances(graph, source))
