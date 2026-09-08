"""Level-triggered reconciliation: drive actual toward desired from state, not from events.

A controller keeping a registry's actual endpoints in line with a
desired specification can be built two ways, and only one is robust.
The edge-triggered way reacts to each change event, create this,
delete that, and it is efficient until an event is lost, at which
point actual and desired drift apart permanently because nothing
ever revisits the discrepancy the missed event left behind. The
level-triggered way ignores events as instructions and instead, on
every pass, recomputes the full difference between the desired state
and the actual state and applies whatever create, delete, and update
operations close the gap. A lost event costs nothing more than a
slightly later convergence, because the next reconcile pass sees the
same discrepancy in the state and fixes it regardless of how it
arose. The price is recomputing the whole diff each pass rather than
handling a single delta, which is the deliberate trade of a little
steady work for immunity to lost, duplicated, or reordered events.
The module computes the create, delete, and update sets from desired
and actual, which is the one operation the reconcile loop repeats.
"""

from __future__ import annotations


def reconcile(
    desired: dict[str, str], actual: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    to_create = sorted(set(desired) - set(actual))
    to_delete = sorted(set(actual) - set(desired))
    to_update = sorted(
        key
        for key in set(desired) & set(actual)
        if desired[key] != actual[key]
    )
    return to_create, to_delete, to_update


def converged(desired: dict[str, str], actual: dict[str, str]) -> bool:
    create, delete, update = reconcile(desired, actual)
    return not (create or delete or update)
