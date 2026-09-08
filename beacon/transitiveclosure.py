"""Transitive closure: precompute all reachability so a can-A-reach-B query is instant.

Asking repeatedly whether one node can reach another over a directed
graph, whether a change to one service can propagate to another,
whether one zone depends transitively on a second, is slow if each
query runs a fresh traversal. The transitive closure precomputes the
answer for every pair. For each node it runs a traversal to find
everything reachable from it, following edges as far as they lead,
and records that reachable set, so afterward a reachability query is
a single set membership test rather than a search. The build costs a
traversal per node, the number of nodes times the graph size, and the
result costs the square of the node count to store since every node
gets a set of the nodes it reaches, which is the price paid up front
to make every later query constant time, worth it when reachability
is asked far more often than the graph changes. The honest limit is
exactly that staleness: a change to the graph invalidates the
precomputed closure and forces a rebuild, so a graph that changes as
often as it is queried is better served by an on-demand traversal or
an incremental structure. The module builds the closure as a map from
each node to the set it can reach, and answers whether one node
reaches another from it.
"""

from __future__ import annotations

from collections import deque


def closure(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    nodes = set(graph)
    for targets in graph.values():
        nodes |= targets
    result: dict[str, set[str]] = {}
    for start in nodes:
        reached: set[str] = set()
        queue = deque(graph.get(start, set()))
        while queue:
            node = queue.popleft()
            if node in reached:
                continue
            reached.add(node)
            queue.extend(graph.get(node, set()))
        result[start] = reached
    return result


def reaches(closed: dict[str, set[str]], source: str, target: str) -> bool:
    return target in closed.get(source, set())
