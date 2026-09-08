"""Deadline propagation: refuse the work whose answer will arrive after nobody is waiting.

A request enters with a deadline, and as it fans out through
hops each hop inherits what is left of it, not a fresh timer.
The failure this prevents is subtle and wasteful: a hop with
fifty milliseconds of budget remaining starts a query that takes
two hundred, and by the time it finishes the caller has long
since given up and returned an error, so the work was pure heat,
consuming a backend's capacity to produce an answer nobody will
read. Deadline propagation makes each hop check the remaining
budget against the estimated cost before starting, and refuse
immediately if the work cannot finish in time, turning a slow
useless success into a fast honest failure. Propagating to a
child also subtracts a margin for the network trip home, because
a child that used the parent's full remaining budget would
return exactly as the parent's deadline expired, wasting the
child's whole effort on a lap it could not complete, and the
module refuses to hand down a budget that is already gone.
"""

from __future__ import annotations

from beacon.errors import Expired, Invalid


class Deadline:
    def __init__(self, budget_ms: int) -> None:
        if budget_ms <= 0:
            raise Invalid(
                "a deadline of zero or less is already expired; "
                "there is no work it could authorize"
            )
        self.budget_ms = budget_ms

    def remaining(self, elapsed_ms: int) -> int:
        return self.budget_ms - elapsed_ms

    def may_start(self, elapsed_ms: int, cost_ms: int) -> bool:
        left = self.remaining(elapsed_ms)
        if left <= 0:
            raise Expired(
                "the deadline is already gone; starting any work "
                "now produces an answer nobody is waiting for"
            )
        return left >= cost_ms

    def child_budget(self, elapsed_ms: int, network_margin_ms: int) -> int:
        left = self.remaining(elapsed_ms) - network_margin_ms
        if left <= 0:
            raise Expired(
                "after the network margin nothing is left to hand "
                "the child; a budget already spent is not worth "
                "propagating"
            )
        return left

    def wasted_if_ignored(self, elapsed_ms: int, cost_ms: int) -> int:
        left = self.remaining(elapsed_ms)
        if cost_ms <= left:
            return 0
        return cost_ms
