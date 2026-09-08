"""Key rollover: retire a signing key without a moment of unsigned air.

Replacing a zone's signing key is a dance with resolver caches
that still hold the old key, and doing it wrong is a signed
zone that briefly cannot be validated, which is worse than an
unsigned zone because it fails closed. The safe rollover is
pre-publish: introduce the new key alongside the old and wait
one full TTL so every cache learns it, then sign with the new
key while the old public key still validates the transition,
then retire the old key only after another TTL so no cache is
left holding a signature it cannot check. The stage machine
here enforces the waits and refuses to skip them, because the
whole point is that at no instant does a validating resolver
hold a signature whose key it lacks, and a rollover that
cannot prove it kept that invariant is just a key change with
optimism. The timeline report states the total safe duration,
which is always at least two TTLs, so the operator who wanted
it done in an afternoon learns the number before the outage
teaches it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

STAGES = (
    "stable",
    "pre-published",
    "new-active",
    "old-retired",
)


@dataclass
class Rollover:
    ttl: int
    stage: str = "stable"
    stage_entered_at: int = 0
    log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.ttl < 1:
            raise Invalid("a zero ttl leaves no window to wait out")

    def _advance(self, to_stage: str, now: int) -> None:
        self.stage = to_stage
        self.stage_entered_at = now
        self.log.append(f"[{now}] entered {to_stage}")

    def pre_publish(self, now: int) -> str:
        if self.stage != "stable":
            raise Invalid(
                f"pre-publish starts from stable, not "
                f"{self.stage}"
            )
        self._advance("pre-published", now)
        return (
            "new key published alongside the old; every cache "
            f"needs one ttl ({self.ttl}) to learn it before "
            "anything signs with it"
        )

    def activate(self, now: int) -> str:
        if self.stage != "pre-published":
            raise Invalid("activation follows pre-publish only")
        waited = now - self.stage_entered_at
        if waited < self.ttl:
            raise Invalid(
                f"only {waited} of {self.ttl} tick(s) waited; "
                "signing now leaves caches holding a signature "
                "whose key they never learned, failing closed"
            )
        self._advance("new-active", now)
        return (
            "signing with the new key; the old public key "
            "still validates the transition, so no resolver "
            "sees unsigned air"
        )

    def retire(self, now: int) -> str:
        if self.stage != "new-active":
            raise Invalid("retirement follows activation only")
        waited = now - self.stage_entered_at
        if waited < self.ttl:
            raise Invalid(
                f"only {waited} of {self.ttl} tick(s) waited; "
                "retiring the old key now strands caches still "
                "holding signatures made under it"
            )
        self._advance("old-retired", now)
        return (
            "old key retired; no cache holds a signature it "
            "cannot check, the invariant kept end to end"
        )

    def timeline_report(self) -> str:
        return (
            f"a safe rollover at ttl {self.ttl} takes at least "
            f"{2 * self.ttl} tick(s), two full ttls of "
            "waiting, and the operator who wanted an afternoon "
            "learns the number here instead of from the outage"
        )
