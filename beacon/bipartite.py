"""Bipartite check: two-color a graph, or prove an odd cycle makes it impossible.

A graph is bipartite when its nodes split into two groups such that
every edge crosses between the groups and none stays within one, and
the question comes up wherever things must be partitioned into two
non-conflicting sets, machines onto two power feeds, tasks into two
phases that must not share a slot. The test is a traversal that
two-colors the graph: start any node one color, color every neighbor
the opposite, and continue, and the graph is bipartite exactly when
this never forces an edge between two nodes of the same color. The
deep fact behind it is that a graph is bipartite if and only if it
contains no odd-length cycle, so a same-color edge discovered during
coloring is the witness of an odd cycle that proves bipartiteness
impossible. Disconnected graphs are handled by coloring each
component independently, since the groups in separate components are
free to align either way. The module two-colors the graph across all
its components by breadth-first traversal and reports whether it is
bipartite, so the partition question and the odd-cycle obstruction
are decided in one linear pass.
"""

from __future__ import annotations

from collections import deque


def is_bipartite(graph: dict[str, set[str]]) -> bool:
    adjacency: dict[str, set[str]] = {}
    for node, neighbors in graph.items():
        adjacency.setdefault(node, set()).update(neighbors)
        for neighbor in neighbors:
            adjacency.setdefault(neighbor, set()).add(node)
    color: dict[str, int] = {}
    for start in adjacency:
        if start in color:
            continue
        color[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in adjacency[node]:
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False
    return True
