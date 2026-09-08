"""RFC 5011 rollover: a new key must survive the hold-down before it is trusted.

A validating resolver pins a trust anchor, the zone's key-signing
key, and when the zone rolls that key the resolver must learn
the new one without an operator hand-editing a file, but it
cannot simply trust any freshly signed key it sees, because a
single compromised signing could inject an attacker's anchor and
every future answer would validate against it. RFC 5011 imposes
a waiting period. A newly observed key enters a pending state
and must be seen continuously for the add-hold-down time, thirty
days by default, before it is trusted, so a key that flickers
into view for an hour during an attack never crosses the
threshold. Removal is the mirror: a trusted key seen with the
revoke bit is retired, and the resolver refuses to revoke a key
it never trusted, since a revoke it cannot attribute is noise.
The module refuses to promote a pending key early because the
hold-down is not a formality around the defense, it is the
defense.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class TrustAnchors:
    add_hold_down: int = 30
    first_seen: dict[str, int] = field(default_factory=dict)
    revoked: set[str] = field(default_factory=set)

    def observe(
        self, key_id: str, now: int, revoke_bit: bool = False
    ) -> None:
        if revoke_bit:
            if key_id not in self.first_seen:
                raise Invalid(
                    f"cannot revoke {key_id}: it was never seen, "
                    "so a revoke for it is unattributable noise"
                )
            self.revoked.add(key_id)
            return
        self.first_seen.setdefault(key_id, now)

    def is_trusted(self, key_id: str, now: int) -> bool:
        if key_id in self.revoked:
            return False
        seen = self.first_seen.get(key_id)
        if seen is None:
            return False
        return now - seen >= self.add_hold_down

    def is_pending(self, key_id: str, now: int) -> bool:
        seen = self.first_seen.get(key_id)
        if seen is None or key_id in self.revoked:
            return False
        return now - seen < self.add_hold_down

    def active(self, now: int) -> set[str]:
        return {
            key_id
            for key_id in self.first_seen
            if self.is_trusted(key_id, now)
        }
