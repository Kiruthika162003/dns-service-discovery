"""A countdown latch: one waiter proceeds once N events have each happened, once.

Some coordination is one-directional: a step should begin only after
a fixed number of prerequisite events have all occurred, all shards
have reported in, all workers have loaded their data, and once they
have there is no going back. A countdown latch expresses exactly
that. It starts at a count, each prerequisite event counts it down by
one, and a waiter is released the moment the count reaches zero. It
differs from a barrier in two ways worth keeping straight. A barrier
is symmetric and reusable, every party waits for every other and the
barrier resets for the next phase, whereas a latch is one-shot and
one-directional, it only ever counts down, never back up, and once
open it stays open. That makes it simpler and the right tool when the
condition is a threshold of distinct events rather than a rendezvous
of peers. The module tracks the remaining count, counts down without
passing below zero so a stray extra event does not corrupt the
threshold, and reports whether the latch has opened, so the readiness
of the guarded step is a decidable state rather than a guess.
"""

from __future__ import annotations

from beacon.errors import Invalid


class CountdownLatch:
    def __init__(self, count: int) -> None:
        if count < 1:
            raise Invalid(
                "a latch of count zero is already open and guards "
                "nothing; start it at the number of events to await"
            )
        self.remaining = count

    def count_down(self) -> None:
        self.remaining = max(0, self.remaining - 1)

    def ready(self) -> bool:
        return self.remaining == 0
