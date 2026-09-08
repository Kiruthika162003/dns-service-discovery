"""Prim's minimum spanning tree: grow one tree, always taking the cheapest edge leaving it.

Prim's algorithm builds the same minimum spanning tree as Kruskal's
but by a different strategy, growing a single tree rather than merging
many. It starts from one node and repeatedly adds the cheapest edge
that connects a node already in the tree to one not yet in it,
extending the tree by one node each step until every node is
included. A heap over the frontier edges, those crossing from the
tree to the outside, makes finding that cheapest edge fast. Because
it always adds an edge leaving the current tree, it never forms a
cycle and never leaves the tree disconnected while nodes remain
reachable. Prim and Kruskal are the two classic MST algorithms and
suit different graphs: Prim, maintaining a frontier per node, tends to
win on dense graphs where edges are plentiful, while Kruskal, sorting
all edges once, wins on sparse graphs where they are few, so the
choice is the graph's density, not a preference. The module grows the
tree from a start node with a heap frontier, returns its edges and
total weight, and refuses when the graph is disconnected and some node
can never be reached to join the tree.
"""

from __future__ import annotations

import heapq

from beacon.errors import Invalid


def minimum_spanning_tree(
    nodes: set[str],
    adjacency: dict[str, dict[str, int]],
    start: str,
) -> tuple[list[tuple[int, str, str]], int]:
    if start not in nodes:
        raise Invalid(f"the start node {start} is not in the node set")
    in_tree = {start}
    frontier = [
        (weight, start, to) for to, weight in adjacency.get(start, {}).items()
    ]
    heapq.heapify(frontier)
    chosen: list[tuple[int, str, str]] = []
    total = 0
    while frontier and len(in_tree) < len(nodes):
        weight, frm, to = heapq.heappop(frontier)
        if to in in_tree:
            continue
        in_tree.add(to)
        chosen.append((weight, frm, to))
        total += weight
        for neighbor, edge_weight in adjacency.get(to, {}).items():
            if neighbor not in in_tree:
                heapq.heappush(frontier, (edge_weight, to, neighbor))
    if len(in_tree) != len(nodes):
        raise Invalid(
            "the graph is disconnected; some node cannot be reached "
            "to join the tree, so no spanning tree exists"
        )
    return chosen, total
