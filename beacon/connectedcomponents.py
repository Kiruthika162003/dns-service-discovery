"""Connected components: one linear traversal groups an undirected graph into its islands.

Asking which nodes can reach each other in an undirected graph, which
members form one gossip cluster, which endpoints share a partition,
is the connected-components question, and a single traversal answers
it. Starting from any unvisited node, a breadth-first sweep visits
everything reachable from it, and those nodes form one component; when
the sweep is exhausted, any node still unvisited starts a new
component, and so on until every node is assigned, which takes one
linear pass over the nodes and edges. This is the batch counterpart
to union-find: a traversal computes all components at once for a
static graph handed over whole, while union-find maintains
connectivity incrementally as edges arrive and answers queries in
between, so the traversal is simpler when the graph is fixed and
union-find better when it grows. The module builds the components as
a list of node sets from an adjacency map, treating the graph as
undirected by following edges both ways, and decides whether two
nodes fall in the same component, so the grouping and the reachability
query are both available from one pass.
"""

from __future__ import annotations

from collections import deque


def components(graph: dict[str, set[str]]) -> list[set[str]]:
    adjacency: dict[str, set[str]] = {}
    for node, neighbors in graph.items():
        adjacency.setdefault(node, set()).update(neighbors)
        for neighbor in neighbors:
            adjacency.setdefault(neighbor, set()).add(node)
    seen: set[str] = set()
    found: list[set[str]] = []
    for start in adjacency:
        if start in seen:
            continue
        component: set[str] = set()
        queue = deque([start])
        seen.add(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        found.append(component)
    return found


def same_component(graph: dict[str, set[str]], a: str, b: str) -> bool:
    for component in components(graph):
        if a in component:
            return b in component
    return False
