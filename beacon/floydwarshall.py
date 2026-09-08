"""Floyd-Warshall: all-pairs shortest paths by allowing one more waypoint at a time.

Where Bellman-Ford answers shortest paths from a single source,
Floyd-Warshall answers them between every pair of vertices at once, and
it does so with an idea so compact it fits in three nested loops. It
considers the vertices one at a time as permitted intermediate points:
after vertex k has been admitted, the stored distance from i to j is the
best path that may pass only through the vertices seen so far, and
admitting k means asking whether going from i to k and then k to j beats
the current best. Sweeping k across all vertices leaves every entry
holding the true shortest distance. The appeal is the flat simplicity
and the fact that it handles negative edges for free; the cost is cubic
time and quadratic space, so it suits dense graphs of modest size rather
than the sparse giants where repeated Dijkstra wins. This module returns
the full distance matrix, and like Bellman-Ford it detects a negative
cycle, which here shows up unmistakably as a vertex whose distance to
itself has gone below zero. It refuses an edge that names a vertex
outside the graph.
"""

from __future__ import annotations

from beacon.errors import Invalid

Edge = tuple[int, int, float]


def all_pairs(vertex_count: int, edges: list[Edge]) -> list[list[float]] | None:
    if vertex_count <= 0:
        raise Invalid(
            f"the graph has {vertex_count} vertices; it must have at least one"
        )
    for tail, head, _ in edges:
        if not 0 <= tail < vertex_count or not 0 <= head < vertex_count:
            raise Invalid(
                f"edge ({tail}, {head}) names a vertex outside the range 0 to "
                f"{vertex_count - 1}"
            )
    distance = [
        [0.0 if i == j else float("inf") for j in range(vertex_count)]
        for i in range(vertex_count)
    ]
    for tail, head, weight in edges:
        distance[tail][head] = min(distance[tail][head], weight)
    for k in range(vertex_count):
        row_k = distance[k]
        for i in range(vertex_count):
            through_k = distance[i][k]
            if through_k == float("inf"):
                continue
            row_i = distance[i]
            for j in range(vertex_count):
                candidate = through_k + row_k[j]
                row_i[j] = min(row_i[j], candidate)
    for i in range(vertex_count):
        if distance[i][i] < 0:
            return None
    return distance
