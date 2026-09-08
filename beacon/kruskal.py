"""Kruskal's minimum spanning tree: take the cheapest edge joining two islands, never a cycle.

Connecting a set of nodes at least total cost, the cheapest overlay
that links every service, is the minimum-spanning-tree problem, and
Kruskal's algorithm solves it greedily. It sorts every edge by weight
and considers them cheapest first, adding an edge to the tree only if
its two endpoints are not already connected, because an edge between
two nodes already in the same component would form a cycle and add
cost without joining anything new. Testing whether the endpoints are
already connected is exactly what union-find does in near-constant
time, so Kruskal is the classic pairing of a greedy edge sort with a
disjoint-set structure. The tree is complete when it has one fewer
edge than there are nodes, at which point everything is one component.
The honest edge case is a disconnected graph: if the edges run out
before the components merge into one, no spanning tree exists,
because some nodes simply cannot be reached, and the module reports
that rather than returning a partial tree pretending to span. The
module builds the tree with union-find cycle tests, returns its edges
and total weight, and refuses when the graph cannot be spanned.
"""

from __future__ import annotations

from beacon.errors import Invalid
from beacon.unionfind import UnionFind


def minimum_spanning_tree(
    nodes: set[str], edges: list[tuple[int, str, str]]
) -> tuple[list[tuple[int, str, str]], int]:
    uf = UnionFind()
    for node in nodes:
        uf.find(node)
    chosen: list[tuple[int, str, str]] = []
    total = 0
    for weight, u, v in sorted(edges):
        if not uf.connected(u, v):
            uf.union(u, v)
            chosen.append((weight, u, v))
            total += weight
    if len(chosen) != len(nodes) - 1:
        raise Invalid(
            "the graph is disconnected; no spanning tree exists "
            "because some nodes cannot be reached from the rest"
        )
    return chosen, total
