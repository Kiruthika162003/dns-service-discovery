"""Bulkhead isolation: a separate pool per dependency, so one slow one cannot sink the ship.

A ship is divided into watertight compartments so a breach in one
does not flood the whole hull, and the pattern named after them
does the same for a service's concurrency. Without it, every call
to every dependency draws from one shared pool of threads or
connections, and a single slow dependency is a catastrophe: its
calls pile up holding the shared resource, and calls to every
other dependency, healthy ones, queue behind them until the whole
service is wedged by one sick downstream. A bulkhead gives each
dependency its own bounded pool, so when one saturates it can only
exhaust its own compartment, and calls to the others keep flowing
from theirs. The trade is deliberate underutilization, since
capacity reserved for one dependency cannot be lent to another
even when idle, which is the cost of the isolation, and the module
enforces the per-dependency limits, refuses a call into a
saturated compartment while leaving the rest untouched, and
reports which compartment is full so the blast radius is named
rather than guessed.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class Bulkhead:
    def __init__(self, limits: dict[str, int]) -> None:
        if not limits:
            raise Invalid("a bulkhead with no compartments isolates nothing")
        for dependency, limit in limits.items():
            if limit < 1:
                raise Invalid(
                    f"{dependency} has a limit of {limit}; a "
                    "compartment that admits no call is a wall, not "
                    "a bulkhead"
                )
        self.limits = dict(limits)
        self.inuse = dict.fromkeys(limits, 0)

    def acquire(self, dependency: str) -> None:
        if dependency not in self.limits:
            raise Invalid(
                f"{dependency} has no compartment; a call to an "
                "unbulkheaded dependency would draw from nowhere"
            )
        if self.inuse[dependency] >= self.limits[dependency]:
            raise Refused(
                f"the {dependency} compartment is full; its calls "
                "are contained here and the other dependencies are "
                "untouched"
            )
        self.inuse[dependency] += 1

    def release(self, dependency: str) -> None:
        if self.inuse.get(dependency, 0) == 0:
            raise Invalid(
                f"nothing is in flight to {dependency} to release; "
                "a double release would drift its count negative"
            )
        self.inuse[dependency] -= 1

    def saturated(self) -> list[str]:
        return sorted(
            dependency
            for dependency, limit in self.limits.items()
            if self.inuse[dependency] >= limit
        )
