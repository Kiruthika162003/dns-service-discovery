"""Deadlock detection: find a cycle in the wait-for graph, then break it by aborting a victim.

Locking disciplines like two-phase locking prevent one kind of error
and admit another: two transactions can each hold a lock the other
wants, and each waits for the other forever, a deadlock. One way to
handle it is to let deadlocks form and detect them, which is cheaper
than preventing them when they are rare, because prevention aborts
transactions eagerly on suspicion while detection lets everyone
proceed and only intervenes when a real cycle appears. Detection
works on the wait-for graph, a directed graph with an edge from a
transaction to each transaction it is blocked waiting on, and a
deadlock is exactly a cycle in that graph: a chain of transactions
each waiting on the next, closing back on itself. When a cycle is
found the system breaks it by choosing a victim in the cycle and
aborting it, releasing its locks so the others can proceed, and the
victim retries later. The module builds on the wait-for graph,
detects whether it contains a cycle, and returns a cycle when one
exists so a victim can be chosen from it, turning deadlock from a
hang into a recoverable event. It reports no cycle when the graph is
acyclic, which is the common, healthy case.
"""

from __future__ import annotations


def find_cycle(wait_for: dict[str, set[str]]) -> list[str]:
    color: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        color[node] = 1
        stack.append(node)
        for neighbor in wait_for.get(node, set()):
            if color.get(neighbor, 0) == 1:
                index = stack.index(neighbor)
                return stack[index:]
            if color.get(neighbor, 0) == 0:
                found = visit(neighbor)
                if found:
                    return found
        stack.pop()
        color[node] = 2
        return []

    for start in wait_for:
        if color.get(start, 0) == 0:
            cycle = visit(start)
            if cycle:
                return cycle
    return []


def has_deadlock(wait_for: dict[str, set[str]]) -> bool:
    return bool(find_cycle(wait_for))
