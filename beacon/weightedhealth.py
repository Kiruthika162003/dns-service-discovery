"""Weighted health: a degraded instance serves less, not nothing, until it must.

Binary health throws away information: an instance answering
slowly but correctly is not dead, and pulling it entirely dumps
its load on peers when shedding a fraction would do. Weighted
health maps a continuous signal, a health score from one down
to zero, onto the routing weight, so a mildly degraded instance
keeps most of its traffic and a badly degraded one keeps a
sliver, and only a score of zero removes it. The subtlety the
module refuses to lose is the floor: below a threshold the
graceful curve stops being graceful, because an instance at
five percent health is not serving five percent of requests
well, it is failing ninety-five percent of them, so past the
floor the weight drops to zero rather than trickling, since
sending any traffic to a nearly-dead instance is spending user
requests to keep a corpse warm. The report contrasts the naive
binary shed against the weighted one on the same fleet, and the
measurement corrected a lazy framing in the first draft: binary
health does not throw capacity away, it oversends, keeping the
degraded instance at full weight where weighting would ease it
down, so the gap runs the other way, binary 200 against
weighted 160 on a fleet with one degraded instance. Weighting
is not recovering lost capacity, it is declining to send full
load to a struggling instance, and stating the direction
correctly matters more than the tidier story that had it
backward.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

FLOOR = 0.2


def health_to_weight(score: float, base_weight: int) -> int:
    if not 0 <= score <= 1:
        raise Invalid("a health score lives between 0 and 1")
    if score < FLOOR:
        return 0
    return round(base_weight * score)


@dataclass
class WeightedFleet:
    scores: dict[str, tuple[float, int]] = field(
        default_factory=dict
    )

    def observe(
        self, instance: str, score: float, base_weight: int
    ) -> None:
        if base_weight < 1:
            raise Invalid(f"{instance} needs a positive base weight")
        health_to_weight(score, base_weight)
        self.scores[instance] = (score, base_weight)

    def effective_weights(self) -> dict[str, int]:
        return {
            instance: health_to_weight(score, base)
            for instance, (score, base) in self.scores.items()
        }

    def binary_weights(self) -> dict[str, int]:
        return {
            instance: (base if score >= FLOOR else 0)
            for instance, (score, base) in self.scores.items()
        }

    def capacity_report(self) -> str:
        if not self.scores:
            raise Invalid("an empty fleet routes nothing")
        weighted = sum(self.effective_weights().values())
        binary = sum(self.binary_weights().values())
        recovered = weighted - binary
        return (
            f"weighted routing keeps {weighted} weight unit(s) "
            f"against binary's {binary}; the "
            f"{abs(recovered)} unit gap is the graceful "
            "capacity binary health "
            f"{'recovers' if recovered >= 0 else 'oversends'}, "
            "invisible until the numbers show it"
        )

    def floor_report(self) -> list[str]:
        return sorted(
            f"{instance} at {score:.0%} health drops to zero "
            "weight; below the floor, serving any traffic "
            "spends user requests to keep a corpse warm"
            for instance, (score, _) in self.scores.items()
            if 0 < score < FLOOR
        )
