"""Euler's condition: walk every edge once, decided by counting odd-degree vertices.

Whether a graph can be traversed so that every edge is used exactly
once, an Eulerian path, or so that such a walk also returns to its
start, an Eulerian circuit, sounds like a search problem but Euler
reduced it to a local count. An undirected connected graph has an
Eulerian circuit precisely when every vertex has even degree, because
each visit to a vertex uses one edge to enter and one to leave, so an
odd degree would strand the walk, and it has an Eulerian path that
need not return to its start precisely when exactly zero or two
vertices have odd degree, the two odd vertices being the path's ends.
That a global property, traversability, is settled by counting odd
degrees at each vertex is the elegant heart of it. The one thing the
count alone misses and the module includes is connectivity: the edges
must form a single connected piece, since a graph in two disconnected
halves cannot be traversed in one walk however even its degrees. The
module counts odd-degree vertices, checks that the edges are
connected, and decides both an Eulerian circuit and an Eulerian path,
so the traversability question is answered by the local condition
plus the one global check it requires.
"""

from __future__ import annotations

from beacon.bfs import reachable


def _degrees(graph: dict[str, set[str]]) -> dict[str, int]:
    return {node: len(neighbors) for node, neighbors in graph.items()}


def _edges_connected(graph: dict[str, set[str]]) -> bool:
    with_edges = [node for node, deg in _degrees(graph).items() if deg > 0]
    if not with_edges:
        return True
    seen = reachable(graph, with_edges[0])
    return all(node in seen for node in with_edges)


def _odd_count(graph: dict[str, set[str]]) -> int:
    return sum(1 for deg in _degrees(graph).values() if deg % 2 == 1)


def has_eulerian_circuit(graph: dict[str, set[str]]) -> bool:
    return _edges_connected(graph) and _odd_count(graph) == 0


def has_eulerian_path(graph: dict[str, set[str]]) -> bool:
    return _edges_connected(graph) and _odd_count(graph) in (0, 2)
