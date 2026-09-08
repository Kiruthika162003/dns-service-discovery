"""Weighted least request: route by outstanding requests scaled to capacity, not by raw count.

Least request routing sends work to the backend with the fewest
requests in flight, which is self-correcting but blind to capacity:
if a small backend and a large one each hold five in-flight requests,
plain least request sees them as equal, though the large one has far
more headroom. Weighted least request scales the in-flight count by
capacity. Each backend carries a weight, and the balancer routes to
the backend with the lowest ratio of outstanding-plus-one to weight,
so a backend twice as capable is kept about twice as loaded before it
stops being the least-loaded choice, and the in-flight signal steers
traffic away from a backend that is slow, while the weight keeps a
small backend from being handed a large one's share. The plus-one in
the numerator matters: it lets an idle backend still be compared
sensibly rather than dividing zero. The module tracks the outstanding
count per backend, computes the capacity-scaled cost, acquires by
routing to the lowest cost and incrementing, releases on completion,
and breaks ties deterministically so the routing is testable rather
than a coin flip.
"""

from __future__ import annotations

from beacon.errors import Invalid


class WeightedLeastRequest:
    def __init__(self, weights: dict[str, float]) -> None:
        if not weights:
            raise Invalid("no backends to balance across")
        for backend, weight in weights.items():
            if weight <= 0:
                raise Invalid(
                    f"{backend} has weight {weight}; a backend in "
                    "the rotation needs a positive capacity"
                )
        self.weights = dict(weights)
        self.active = dict.fromkeys(weights, 0)

    def cost(self, backend: str) -> float:
        return (self.active[backend] + 1) / self.weights[backend]

    def choose(self) -> str:
        return min(
            self.weights, key=lambda b: (self.cost(b), b)
        )

    def acquire(self) -> str:
        chosen = self.choose()
        self.active[chosen] += 1
        return chosen

    def release(self, backend: str) -> None:
        if backend not in self.active:
            raise Invalid(f"{backend} is not in this balancer")
        if self.active[backend] == 0:
            raise Invalid(
                f"{backend} has nothing in flight to release; a "
                "double release would undercount its load"
            )
        self.active[backend] -= 1

    def load(self) -> dict[str, int]:
        return dict(self.active)
