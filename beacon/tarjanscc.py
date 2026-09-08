"""Tarjan's algorithm: find strongly connected components in a single depth-first walk.

A strongly connected component of a directed graph is a maximal set of
vertices where every vertex can reach every other, and finding these
components is how you collapse cyclic tangles into single nodes before
reasoning about a graph as an acyclic whole, whether the graph is a web
of package dependencies, a call graph, or a mesh of services that call
each other. Tarjan's algorithm finds them all in one depth-first
traversal. As it descends it stamps each vertex with the order it was
discovered and tracks, for each vertex, the earliest-discovered vertex
reachable from its subtree by following tree edges and at most one edge
back to a vertex still on the traversal stack. When a vertex's own
discovery stamp equals that earliest reachable stamp, it is the root of
a component, and everything above it on the stack forms that component.
The result is linear in the graph's size, a single pass where the naive
approach would run a separate reachability search from every vertex.
The honest caveat is depth: this implementation recurses, so a graph
with a very long path can exhaust the interpreter's call stack, and such
a graph needs the explicit-stack rewrite that trades this clarity for
robustness. This module returns the components, each as a sorted list.
"""

from __future__ import annotations

from beacon.errors import Invalid


def components(vertex_count: int, adjacency: dict[int, list[int]]) -> list[list[int]]:
    if vertex_count < 0:
        raise Invalid(
            f"the graph has {vertex_count} vertices; the count cannot be negative"
        )
    for tail, heads in adjacency.items():
        if not 0 <= tail < vertex_count:
            raise Invalid(
                f"vertex {tail} is outside the range 0 to {vertex_count - 1}"
            )
        for head in heads:
            if not 0 <= head < vertex_count:
                raise Invalid(
                    f"edge ({tail}, {head}) names a vertex outside the range 0 "
                    f"to {vertex_count - 1}"
                )
    index_of: list[int | None] = [None] * vertex_count
    low_link = [0] * vertex_count
    on_stack = [False] * vertex_count
    stack: list[int] = []
    counter = 0
    result: list[list[int]] = []

    def strong_connect(vertex: int) -> None:
        nonlocal counter
        index_of[vertex] = counter
        low_link[vertex] = counter
        counter += 1
        stack.append(vertex)
        on_stack[vertex] = True
        for neighbor in adjacency.get(vertex, []):
            if index_of[neighbor] is None:
                strong_connect(neighbor)
                low_link[vertex] = min(low_link[vertex], low_link[neighbor])
            elif on_stack[neighbor]:
                low_link[vertex] = min(low_link[vertex], index_of[neighbor])
        if low_link[vertex] == index_of[vertex]:
            component: list[int] = []
            while True:
                member = stack.pop()
                on_stack[member] = False
                component.append(member)
                if member == vertex:
                    break
            result.append(sorted(component))

    for vertex in range(vertex_count):
        if index_of[vertex] is None:
            strong_connect(vertex)
    return sorted(result)
