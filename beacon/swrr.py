"""Smooth weighted round robin: the same proportions as naive weighting, without the bursts.

Weighted round robin has to hand a heavier server more turns, and
the naive way, emit a server as many times in a row as its weight,
gets the proportions right and the timing wrong: a server weighted
five receives five requests back to back, a burst that spikes its
latency while the light servers sit idle, so the average load is
correct and the instantaneous load is lumpy. Smooth weighted round
robin, the scheme in nginx, keeps a running current weight per
server, adds each server's weight to its own counter every step,
serves the server whose counter is highest, and then subtracts the
total weight from the one it served. Over a full cycle each server
is chosen exactly its weight's worth of times, so the proportions
are identical to the naive scheme, but the picks are interleaved
rather than clustered, which is the whole point. The module holds
the two invariants that make it correct: the counts over a cycle
match the weights, and the counters return to their starting point
so the pattern repeats cleanly forever.
"""

from __future__ import annotations

from beacon.errors import Invalid


class SmoothWeighted:
    def __init__(self, weights: dict[str, int]) -> None:
        if not weights:
            raise Invalid("no servers to weight")
        for name, weight in weights.items():
            if weight <= 0:
                raise Invalid(
                    f"{name} has weight {weight}; a server in the "
                    "rotation must have a positive weight or it is "
                    "not in the rotation at all"
                )
        self.weights = dict(weights)
        self.current = dict.fromkeys(weights, 0)

    def total(self) -> int:
        return sum(self.weights.values())

    def pick(self) -> str:
        total = self.total()
        for name, weight in self.weights.items():
            self.current[name] += weight
        chosen = max(
            self.current, key=lambda name: (self.current[name], name)
        )
        self.current[chosen] -= total
        return chosen

    def cycle(self) -> list[str]:
        return [self.pick() for _ in range(self.total())]
