"""Topological sort: order tasks after their dependencies, or prove a cycle forbids it.

Applying configuration, running migrations, or bringing up services
with dependencies needs an order where nothing starts before what it
depends on, and that order is a topological sort of the dependency
graph. Kahn's algorithm builds it by repeatedly taking a node with no
remaining unmet dependencies, emitting it, and removing it from the
graph, which frees whatever depended only on it, until every node is
emitted. If at some point nodes remain but none has zero unmet
dependencies, the graph has a cycle, a set of tasks that each wait on
another in a loop, and no order can satisfy them, which the algorithm
detects rather than spinning forever. That detection is as valuable
as the ordering, because a circular dependency is a real
configuration error the operator must break, not a transient
condition to retry. Ties among independent nodes are broken
deterministically so the output is stable and testable. The module
computes a dependency-respecting order and raises on a cycle, naming
it as the impossibility it is, so both the valid ordering and the
detected loop are explicit outcomes.
"""

from __future__ import annotations

from beacon.errors import Invalid


def topological_sort(dependencies: dict[str, set[str]]) -> list[str]:
    nodes = set(dependencies)
    for deps in dependencies.values():
        nodes |= deps
    unmet = {node: set(dependencies.get(node, set())) for node in nodes}
    order: list[str] = []
    while unmet:
        ready = sorted(node for node, deps in unmet.items() if not deps)
        if not ready:
            raise Invalid(
                f"a dependency cycle among {sorted(unmet)} has no valid "
                "order; a circular dependency must be broken, not retried"
            )
        for node in ready:
            order.append(node)
            del unmet[node]
        ready_set = set(ready)
        for deps in unmet.values():
            deps.difference_update(ready_set)
    return order
