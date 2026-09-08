"""Rate-monotonic scheduling: shorter period, higher fixed priority, predictable under overload.

Rate-monotonic scheduling assigns static priorities by period: the
task that repeats most often, the shortest period, gets the highest
priority, and the assignment never changes at runtime. That fixed
ordering is the point of contrast with earliest-deadline-first, which
is dynamic. It buys predictability, especially under overload: when
the system cannot meet everything, a fixed-priority scheme fails in a
known order, the lowest-priority, longest-period task misses first
while the critical short-period tasks keep running, whereas EDF can
cascade unpredictably. The price is utilization headroom. Rate-
monotonic is guaranteed schedulable only up to the Liu-Layland bound,
which is n times the quantity two-to-the-one-over-n minus one, a value
that starts at one for a single task and falls toward about sixty-nine
percent as the number of tasks grows, so a rate-monotonic system may
have to leave nearly a third of the processor idle to guarantee all
deadlines, where EDF could use it all. The module assigns priority
from period, computes the Liu-Layland bound for a task count, and
decides whether a utilization is within the bound, refusing a
non-positive period that has no rate.
"""

from __future__ import annotations

from beacon.errors import Invalid


def priority(period: int) -> float:
    if period <= 0:
        raise Invalid("a period must be positive to define a rate")
    return 1.0 / period


def liu_layland_bound(n: int) -> float:
    if n < 1:
        raise Invalid("the task count must be at least one")
    return n * (2 ** (1 / n) - 1)


def schedulable(utilization: float, n: int) -> bool:
    if utilization < 0:
        raise Invalid("utilization is never negative")
    return utilization <= liu_layland_bound(n)
