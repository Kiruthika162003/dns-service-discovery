"""RRSIG windows: a validity too brief locks users out, too long invites replay.

Every signed RRset carries an inception and an expiration, and
validation fails outside that window, which makes the window a
live operational hazard rather than a formality. Set the
expiration too close and a signing outage, a resigner stuck for a
day, expires the signatures while the records themselves are
perfectly good, and the entire zone goes bogus for validators
though nothing was ever wrong with the data. Set it too far and a
captured signed answer can be replayed long after the record it
covers has changed. The safe practice is a validity comfortably
longer than the resign interval, so a fresh signature is always
minted well before the old one lapses, with the inception
backdated a little to tolerate validators whose clocks run slow.
The module refuses a signature whose lifetime is not longer than
the resign interval, because that arrangement guarantees a gap the
first time resigning slips, and it reports the runway remaining
before a signature must be refreshed so the operator sees the
outage coming instead of discovering it as a bogus zone.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class Signature:
    inception: int
    expiration: int

    def __post_init__(self) -> None:
        if self.expiration <= self.inception:
            raise Invalid(
                "a signature that expires at or before it begins "
                "is valid for no instant and denies every answer"
            )

    def lifetime(self) -> int:
        return self.expiration - self.inception

    def valid_at(self, now: int, clock_skew: int = 0) -> bool:
        return (
            self.inception - clock_skew
            <= now
            <= self.expiration + clock_skew
        )

    def refresh_due(self, now: int, resign_interval: int) -> bool:
        return now >= self.expiration - resign_interval

    def runway(self, now: int, resign_interval: int) -> int:
        return (self.expiration - resign_interval) - now


def plan_lifetime(resign_interval: int, lifetime: int) -> int:
    if lifetime <= resign_interval:
        raise Invalid(
            f"a lifetime of {lifetime} is not longer than the "
            f"{resign_interval} resign interval; the first slipped "
            "resign expires the zone into bogus while the data is "
            "still good"
        )
    return lifetime - resign_interval
