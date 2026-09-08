"""TTL clamping: the cache trusts the record's clock, within reason.

Authoritative servers set TTLs for their own reasons, and some
of those reasons are mistakes: a TTL of 1 turns a cache into a
relay that hammers the upstream, and a TTL of a week turns a
typo into a week-long incident nobody can flush remotely. The
clamp bounds both ends, floor and ceiling, and the policy's
honesty is in its bookkeeping: every clamped record is counted
by direction, because the two directions indict different
parties. A fleet of floor-clamps means upstream operators are
publishing twitchy TTLs and the cache is defending its own
upstream bill; a fleet of ceiling-clamps means someone is
publishing immortality and the cache is defending its
flushability. The report also names the cost of the clamp
itself, extra refreshes bought by the floor and staleness
risk bought by the ceiling, since a clamp with no recorded
price reads as free and no clamp is free.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

FLOOR = 30
CEILING = 86_400


@dataclass
class ClampLedger:
    floored: int = 0
    ceilinged: int = 0
    untouched: int = 0
    extra_refreshes_bought: int = 0
    staleness_risk_ticks: int = 0

    def clamp(self, name: str, ttl: int) -> tuple[int, str]:
        if ttl < 0:
            raise Invalid("a negative ttl is not a duration")
        if ttl == 0:
            self.untouched += 1
            return 0, (
                f"{name}: ttl 0 passes; do-not-cache is a "
                "statement, not a mistake"
            )
        if ttl < FLOOR:
            self.floored += 1
            self.extra_refreshes_bought += 1
            return FLOOR, (
                f"{name}: ttl {ttl} floored to {FLOOR}; a "
                "twitchy ttl turns the cache into a relay "
                "and the upstream bill is ours"
            )
        if ttl > CEILING:
            self.ceilinged += 1
            self.staleness_risk_ticks += ttl - CEILING
            return CEILING, (
                f"{name}: ttl {ttl} ceilinged to {CEILING}; "
                "published immortality is a typo that cannot "
                "be flushed remotely"
            )
        self.untouched += 1
        return ttl, f"{name}: ttl {ttl} trusted as written"

    def indictment(self) -> str:
        lines = [
            f"{self.untouched} trusted, {self.floored} "
            f"floored, {self.ceilinged} ceilinged"
        ]
        if self.floored > self.untouched:
            lines.append(
                "  the floor column dominates: upstream "
                "operators are publishing twitchy TTLs and "
                "this cache is defending its own bill"
            )
        if self.ceilinged > self.untouched:
            lines.append(
                "  the ceiling column dominates: someone is "
                "publishing immortality and this cache is "
                "defending its flushability"
            )
        lines.append(
            f"  price paid: {self.extra_refreshes_bought} "
            f"extra refresh(es), {self.staleness_risk_ticks} "
            "tick(s) of staleness risk; no clamp is free"
        )
        return "\n".join(lines)
