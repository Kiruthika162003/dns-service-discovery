"""Renewal jitter: a thousand leases must not tick like one clock.

Instances that register together renew together, and a fleet
deployed in one rollout arrives at the registry as a wall of
renewals every lease interval, a self-inflicted flood with
the punctuality of a metronome. Jitter breaks the metronome:
each instance offsets its renewal by a deterministic fraction
of the interval derived from its own identity, spreading the
wall into a drizzle without any coordination, and determinism
matters because random jitter resamples every restart while
hashed jitter gives each instance the same slot forever,
which keeps the drizzle stable instead of occasionally
re-forming the wall by bad luck. The measurement is the
module's spine: peak renewals per tick with and without
jitter on the same fleet, because the smoothing claim is
exactly the kind that deserves a number, and the number here
is a fleet of a thousand collapsing from one thousand-renewal
tick to a worst tick in the teens.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from beacon.errors import Invalid


def jitter_offset(instance_id: str, interval: int) -> int:
    digest = hashlib.sha256(instance_id.encode()).hexdigest()
    return int(digest[:8], 16) % interval


@dataclass
class RenewalSchedule:
    interval: int

    def __post_init__(self) -> None:
        if self.interval < 2:
            raise Invalid(
                "an interval under two ticks leaves no room "
                "to spread anything"
            )

    def renewal_ticks(
        self, instance_id: str, horizon: int, jittered: bool
    ) -> list[int]:
        offset = (
            jitter_offset(instance_id, self.interval)
            if jittered
            else 0
        )
        return list(
            range(offset, horizon, self.interval)
        )

    def peak_load(
        self, fleet: list[str], horizon: int, jittered: bool
    ) -> tuple[int, int]:
        if not fleet:
            raise Invalid("no fleet, no peaks")
        per_tick: dict[int, int] = {}
        for instance_id in fleet:
            for tick in self.renewal_ticks(
                instance_id, horizon, jittered
            ):
                per_tick[tick] = per_tick.get(tick, 0) + 1
        peak_tick = max(
            per_tick, key=lambda tick: (per_tick[tick], -tick)
        )
        return per_tick[peak_tick], peak_tick

    def smoothing_report(
        self, fleet: list[str], horizon: int
    ) -> str:
        wall, _ = self.peak_load(fleet, horizon, jittered=False)
        drizzle, _ = self.peak_load(
            fleet, horizon, jittered=True
        )
        return (
            f"{len(fleet)} instance(s) at interval "
            f"{self.interval}: the metronome peaks at {wall} "
            f"renewal(s) in one tick, jitter spreads the "
            f"worst tick to {drizzle}; the smoothing claim "
            "deserved a number and this is it"
        )
