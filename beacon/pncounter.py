"""A PN-counter: decrements made safe by counting them separately and subtracting.

A grow-only counter cannot go down without breaking the invariant
that lets replicas merge, so a counter that must support both
directions is built from two grow-only counters, one that only
ever counts increments and one that only ever counts decrements,
and the value is the first sum minus the second. The trick is that
neither underlying counter ever decreases, so both merge by the
safe entrywise maximum, and their difference gives a number that
can move either way while the parts that merge only grow. A
decrement is not a subtraction from a total, which would be
unmergeable; it is an increment to the negative counter, which is
mergeable, and that reframing is the whole idea. The module keeps
the two counters and exposes increment and decrement over them,
merges by merging each half, and reports the difference, so a
distributed like-and-unlike tally or a reference count can be
maintained across replicas that reconcile without coordination and
without a single decrement being lost to a merge that kept the
larger total.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.gcounter import GCounter


@dataclass
class PNCounter:
    positive: GCounter = field(default_factory=GCounter)
    negative: GCounter = field(default_factory=GCounter)

    def increment(self, replica: str, by: int = 1) -> None:
        self.positive.increment(replica, by)

    def decrement(self, replica: str, by: int = 1) -> None:
        self.negative.increment(replica, by)

    def value(self) -> int:
        return self.positive.value() - self.negative.value()

    def merge(self, other: PNCounter) -> PNCounter:
        return PNCounter(
            self.positive.merge(other.positive),
            self.negative.merge(other.negative),
        )
