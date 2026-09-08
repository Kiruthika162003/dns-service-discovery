"""Certificate pinning in DNS: TLSA records that outlive their certificates.

A zone can publish the fingerprint of the certificate its
service should present, so a client validates the certificate
against DNS rather than against a certificate authority alone,
which stops a mis-issued certificate from a compromised CA. The
power comes with a foot-gun this module exists to defuse: the
pin outlives the certificate unless someone updates it, so a
certificate rotation that does not update the TLSA record turns
a routine renewal into an outage where the new, valid
certificate is rejected by the client for not matching the old
pin. The manager enforces the same overlap discipline as key
rollover: publish the new pin alongside the old, wait a TTL for
caches to learn it, rotate the certificate while both pins
validate, then retire the old pin. It refuses to retire a pin
still inside its TTL because a client cache holding only the
retired pin would reject the live certificate, and the horizon
report counts down to the next certificate expiry against the
pin's freshness, since a pin update forgotten until the cert
expires is an outage with a date already on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class PinSet:
    ttl: int
    active_pins: set[str] = field(default_factory=set)
    pending_since: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ttl < 1:
            raise Invalid("a zero ttl leaves no window to overlap")

    def publish_new(self, fingerprint: str, now: int) -> str:
        if fingerprint in self.active_pins:
            raise Invalid(f"{fingerprint[:8]} is already active")
        self.active_pins.add(fingerprint)
        self.pending_since[fingerprint] = now
        return (
            f"pin {fingerprint[:8]} published alongside the "
            f"old; caches need one ttl ({self.ttl}) before the "
            "old can retire"
        )

    def validate(self, cert_fingerprint: str) -> str:
        if cert_fingerprint in self.active_pins:
            return (
                f"certificate {cert_fingerprint[:8]} matches an "
                "active pin"
            )
        raise Invalid(
            f"certificate {cert_fingerprint[:8]} matches no "
            "active pin; a valid cert rejected here is a pin "
            "that was not updated before rotation"
        )

    def retire(self, fingerprint: str, now: int) -> str:
        if fingerprint not in self.active_pins:
            raise Invalid(f"{fingerprint[:8]} is not active")
        if len(self.active_pins) == 1:
            raise Invalid(
                "retiring the last pin leaves nothing to "
                "validate against; publish the new one first"
            )
        published_at = self.pending_since.get(fingerprint, now)
        newest_other = max(
            self.pending_since.get(pin, 0)
            for pin in self.active_pins
            if pin != fingerprint
        )
        if now - newest_other < self.ttl:
            raise Invalid(
                f"only {now - newest_other} of {self.ttl} "
                "tick(s) since the replacement published; "
                "retiring now leaves caches holding only the "
                "retired pin, rejecting the live certificate"
            )
        self.active_pins.discard(fingerprint)
        self.pending_since.pop(fingerprint, None)
        del published_at
        return f"pin {fingerprint[:8]} retired; overlap held"

    def expiry_horizon(self, cert_expires_at: int, now: int) -> str:
        remaining = cert_expires_at - now
        if remaining <= self.ttl:
            return (
                f"the certificate expires in {remaining} "
                f"tick(s), inside the pin ttl of {self.ttl}; a "
                "pin update forgotten now is an outage with a "
                "date already on it"
            )
        return (
            f"{remaining} tick(s) to certificate expiry, room "
            "to rotate the pin safely"
        )
