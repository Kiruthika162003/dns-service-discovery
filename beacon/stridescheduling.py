"""Stride scheduling: deterministic proportional share, the client furthest along waits.

Proportional-share scheduling gives each client CPU in proportion to
its weight, and stride scheduling does it deterministically, without
the variance that a random lottery leaves. Each client is assigned a
stride, a large constant divided by its weight, so a heavier client
has a smaller stride, and each client carries a pass value that
starts at zero. The scheduler always runs the client with the lowest
pass, the one that has advanced least through its share, and then
adds that client's stride to its pass, pushing it forward by an
amount inversely proportional to its weight. A heavy client, with its
small stride, creeps forward slowly and so is chosen again soon,
while a light client leaps ahead and waits longer, and over a full
cycle each client is chosen exactly in proportion to its weight, with
no randomness and no drift. That determinism is the difference from
lottery scheduling, which achieves the same proportion only in
expectation and can be unlucky over a short window; stride pays for
its exactness with a little per-client state, the stride and the
pass. The module assigns strides from weights, picks the lowest-pass
client and advances it, and refuses a non-positive weight that has no
meaningful share.
"""

from __future__ import annotations

from beacon.errors import Invalid

_BIG = 1_000_000


class StrideScheduler:
    def __init__(self, weights: dict[str, int]) -> None:
        if not weights:
            raise Invalid("no clients to schedule")
        for client, weight in weights.items():
            if weight <= 0:
                raise Invalid(
                    f"{client} has weight {weight}; a share needs a "
                    "positive weight"
                )
        self.stride = {c: _BIG // w for c, w in weights.items()}
        self.passes = dict.fromkeys(weights, 0)

    def pick(self) -> str:
        chosen = min(self.passes, key=lambda c: (self.passes[c], c))
        self.passes[chosen] += self.stride[chosen]
        return chosen

    def run(self, steps: int) -> dict[str, int]:
        counts = dict.fromkeys(self.passes, 0)
        for _ in range(steps):
            counts[self.pick()] += 1
        return counts
