"""Signed answers: validity windows, clock skew, and the expiry cliff.

A signature on a record set proves who published it, and the
proof carries two timestamps, inception and expiration,
because a signature valid forever is a replay attack's best
friend. Validation walks three checks in order: the signer
must be the zone's declared key, the window must contain now,
and the window itself must be sane, inception before
expiration and neither absurdly long. Clock skew gets the
tolerance the real world demands, a small grace on both
edges, because two machines that disagree by a minute should
not turn every answer invalid at the stroke of inception.
The operational cliff this module keeps in front of
operators: signatures expire on their own schedule whether or
not anyone re-signs, so a zone that stops its signing
pipeline stays valid right up to the wall and then every
record fails at once, and the horizon report counts down to
that wall, because the worst DNSSEC outage is the one that
was scheduled months in advance by nobody reading the dates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Expired, Invalid

SKEW_GRACE = 5
MAX_WINDOW = 2_592_000


@dataclass(frozen=True)
class Signature:
    signer_key: str
    inception: int
    expiration: int

    def __post_init__(self) -> None:
        if self.inception >= self.expiration:
            raise Invalid(
                "a window that ends before it begins signs "
                "nothing"
            )
        if self.expiration - self.inception > MAX_WINDOW:
            raise Invalid(
                f"a {self.expiration - self.inception} tick "
                "window is close enough to forever to be a "
                "replay attack's best friend"
            )


@dataclass
class Validator:
    zone_key: str
    validated: int = 0
    skew_saves: int = 0
    refusal_log: list[str] = field(default_factory=list)

    def validate(self, signature: Signature, now: int) -> str:
        if signature.signer_key != self.zone_key:
            refusal = (
                f"signed by {signature.signer_key}, the zone "
                f"declares {self.zone_key}; whoever this is, "
                "it is not the zone"
            )
            self.refusal_log.append(refusal)
            raise Invalid(refusal)
        if now < signature.inception - SKEW_GRACE:
            refusal = (
                f"inception {signature.inception} is in the "
                f"future beyond the {SKEW_GRACE}-tick grace; "
                "either a replay from tomorrow or a broken "
                "clock, both worth refusing"
            )
            self.refusal_log.append(refusal)
            raise Invalid(refusal)
        if now > signature.expiration + SKEW_GRACE:
            refusal = (
                f"expired at {signature.expiration}, it is "
                f"{now}; the signature ended and nothing "
                "re-signed"
            )
            self.refusal_log.append(refusal)
            raise Expired(refusal)
        if (
            now < signature.inception
            or now > signature.expiration
        ):
            self.skew_saves += 1
            self.validated += 1
            return (
                "valid within the skew grace; two machines a "
                "minute apart should not invalidate the world"
            )
        self.validated += 1
        return "valid"

    def horizon_report(
        self, signatures: list[Signature], now: int
    ) -> str:
        if not signatures:
            raise Invalid("no signatures to watch")
        soonest = min(
            signatures, key=lambda held: held.expiration
        )
        remaining = soonest.expiration - now
        if remaining <= 0:
            return (
                "THE WALL: signatures are already expiring "
                "and every record they cover fails at once"
            )
        line = (
            f"{len(signatures)} signature(s); the nearest "
            f"wall is {remaining} tick(s) away"
        )
        if remaining < MAX_WINDOW // 10:
            line += (
                "; the worst DNSSEC outage is the one "
                "scheduled months in advance by nobody "
                "reading the dates"
            )
        return line
