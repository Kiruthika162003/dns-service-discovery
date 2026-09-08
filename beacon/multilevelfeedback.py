"""Multilevel feedback queue: favor short jobs without knowing their length.

A scheduler wants to run short, interactive jobs quickly and let long,
CPU-bound jobs wait, but it does not know in advance which is which.
A multilevel feedback queue learns it from behavior. Jobs start in
the top queue, the highest priority with the shortest time slice, and
a job that uses its entire slice, the mark of a CPU-bound job, is
demoted to a lower queue with a longer slice, while a job that gives
up the CPU before its slice ends, the mark of an interactive job
waiting on input, stays high. So over time interactive jobs cluster
near the top and stay responsive, and CPU hogs sink to the bottom and
run in long slices when nothing better is ready, all without any
prior knowledge of runtimes. Two hazards the module notes. Without a
periodic boost that lifts everything back to the top, a steady stream
of short jobs can starve the sunk long ones forever, so a boost is
part of the design. And a job can game the scheme by yielding just
before its slice expires, staying high while consuming nearly a full
slice each time, which is why real implementations account total time
at a level rather than per-slice behavior. The module demotes a job
that used its full slice, keeps one that yielded, and boosts all jobs
to the top on demand.
"""

from __future__ import annotations

from beacon.errors import Invalid


class MultilevelFeedbackQueue:
    def __init__(self, levels: int) -> None:
        if levels < 2:
            raise Invalid(
                "a feedback queue needs at least two levels to demote "
                "between"
            )
        self.levels = levels

    def next_level(self, current_level: int, used_full_slice: bool) -> int:
        if not 0 <= current_level < self.levels:
            raise Invalid(
                f"level {current_level} is outside 0..{self.levels - 1}"
            )
        if used_full_slice:
            return min(current_level + 1, self.levels - 1)
        return current_level

    def boost(self) -> int:
        return 0
