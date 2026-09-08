"""Weighted reservoir sampling: a one-pass sample that favors heavy items, not guarantees them.

Uniform reservoir sampling gives every item the same chance of being
kept, but sometimes items are not equally valuable, an error log line
matters more than a routine one, a large customer's request more than
a trivial one, and the sample should reflect that. Weighted reservoir
sampling, the A-Res algorithm, does it in one pass. Each item is
assigned a key computed as a uniform random draw raised to the power
of one over the item's weight, and the reservoir keeps the items with
the largest keys. The exponent is the trick: a larger weight pushes
the key closer to one, so heavier items tend to score higher and are
more likely retained, in a proportion that makes the inclusion
probability track the weight, all without a second pass or knowing
the stream's length. The honest boundary is the same as uniform
sampling, only tilted: a heavy item is favored, not guaranteed, so a
single very important item can still miss the sample, just far less
often than a light one. The module assigns keys from an injected draw
so it is testable, keeps the top keys within the capacity, and
reports the resident sample, so the weighting is a mechanism rather
than a claim.
"""

from __future__ import annotations

from beacon.errors import Invalid


class WeightedReservoir:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a reservoir of zero capacity samples nothing")
        self.capacity = capacity
        self.keyed: list[tuple[float, str]] = []

    def offer(self, item: str, weight: float, draw: float) -> None:
        if weight <= 0:
            raise Invalid("a sampling weight must be positive")
        if not 0.0 < draw <= 1.0:
            raise Invalid(
                f"the draw {draw} must be in (0, 1]; its root anchors "
                "the key and is undefined at zero"
            )
        key = draw ** (1.0 / weight)
        if len(self.keyed) < self.capacity:
            self.keyed.append((key, item))
            self.keyed.sort()
            return
        if key > self.keyed[0][0]:
            self.keyed[0] = (key, item)
            self.keyed.sort()

    def contents(self) -> list[str]:
        return [item for _, item in self.keyed]
