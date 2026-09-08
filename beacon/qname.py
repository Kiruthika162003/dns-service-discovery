"""QNAME minimization: the root does not need to know you asked for mail.

Traditional resolution leaks: to resolve mail.eng.corp.example
the resolver historically asked the root, the com servers, and
the example servers each for the full name, so every server up
the chain learned the exact hostname though it only needed the
next label to do its job. QNAME minimization sends each server
only what it needs: the root is asked about example, the
example servers about corp.example, and only the final
authority ever sees the full mail.eng.corp.example. The
privacy gain is countable, the number of servers that learned
the full name drops from the chain length to one, and this
module measures exactly that on a given name and delegation
depth. The honesty is in the cost: minimization can add a
query per label when a zone cut does not fall where the
resolver guessed, so the ledger reports extra queries against
labels hidden, because privacy that hides its own price tag
is advocacy, not engineering.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid
from beacon.names import Name


@dataclass
class MinimizationResult:
    steps: list[str]
    servers_that_saw_full_name: int
    extra_queries: int


def resolve_traditional(name: Name) -> MinimizationResult:
    if name.is_root():
        raise Invalid("the root resolves itself")
    depth = len(name.labels)
    steps = [
        f"asked a server about the FULL {name.canonical()}"
        for _ in range(depth)
    ]
    return MinimizationResult(
        steps=steps,
        servers_that_saw_full_name=depth,
        extra_queries=0,
    )


def resolve_minimized(
    name: Name, zone_cuts: set[int]
) -> MinimizationResult:
    if name.is_root():
        raise Invalid("the root resolves itself")
    labels = name.labels
    depth = len(labels)
    steps = []
    extra = 0
    for level in range(1, depth + 1):
        revealed = Name(labels=labels[depth - level :])
        steps.append(
            f"revealed only {revealed.canonical()}"
        )
        if level < depth and level not in zone_cuts:
            extra += 1
    return MinimizationResult(
        steps=steps,
        servers_that_saw_full_name=1,
        extra_queries=extra,
    )


def privacy_report(
    name: Name, zone_cuts: set[int]
) -> str:
    traditional = resolve_traditional(name)
    minimized = resolve_minimized(name, zone_cuts)
    hidden = (
        traditional.servers_that_saw_full_name
        - minimized.servers_that_saw_full_name
    )
    return (
        f"{name.canonical()}: traditionally "
        f"{traditional.servers_that_saw_full_name} server(s) "
        f"learned the full name, minimization leaves 1; "
        f"{hidden} fewer eavesdropper(s) at a cost of "
        f"{minimized.extra_queries} extra query(ies), because "
        "privacy that hides its own price tag is advocacy, "
        "not engineering"
    )
