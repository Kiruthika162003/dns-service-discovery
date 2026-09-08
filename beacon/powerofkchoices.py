"""Power of k choices: sampling more candidates flattens the tail, with diminishing returns.

Random placement, sending each request to a uniformly chosen
backend, leaves a surprisingly lumpy load: by the balls-into-bins
result the busiest backend runs well ahead of the average, and that
tail is what hurts. The power of two choices is the famous fix,
sample two backends and use the less loaded, which shrinks the
maximum load from far above average to barely above it, an
exponential improvement from just one extra sample. The
generalization is to sample k, and the module makes the shape of the
returns explicit: going from one choice to two is the enormous jump,
from two to three helps noticeably less, and each further sample
flattens the tail a little more while the marginal benefit shrinks
toward nothing, so k is chosen where the tail is tame enough and the
sampling cost, k reads per placement, is not yet wasteful. The
module assigns a stream of keys by picking the least loaded of k
sampled backends, tracks the resulting per-backend load, and reports
the maximum load over the average so the tail each k achieves is a
measured number, letting an operator see the diminishing returns
rather than guess at k.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _sample(key: str, backends: list[str], k: int) -> list[str]:
    chosen = []
    for probe in range(k):
        digest = hashlib.blake2b(
            f"{probe}:{key}".encode(), digest_size=8
        ).digest()
        index = int.from_bytes(digest, "big") % len(backends)
        chosen.append(backends[index])
    return chosen


class KChoices:
    def __init__(self, backends: list[str], k: int) -> None:
        if not backends:
            raise Invalid("no backends to place load on")
        if not 1 <= k <= len(backends):
            raise Invalid(
                f"k of {k} must be between one and the "
                f"{len(backends)} backends; sampling more than exist "
                "is not a choice"
            )
        self.backends = list(backends)
        self.k = k
        self.load = dict.fromkeys(backends, 0)

    def place(self, key: str) -> str:
        candidates = _sample(key, self.backends, self.k)
        chosen = min(candidates, key=lambda b: (self.load[b], b))
        self.load[chosen] += 1
        return chosen

    def place_all(self, keys: list[str]) -> None:
        for key in keys:
            self.place(key)

    def max_over_average(self) -> float:
        total = sum(self.load.values())
        if total == 0:
            return 0.0
        average = total / len(self.backends)
        return max(self.load.values()) / average
