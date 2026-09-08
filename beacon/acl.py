"""Query ACLs: who may ask, who may transfer, and who hears a clean no.

A zone answers three kinds of askers: anyone may usually
query, only secondaries may transfer, and nobody outside the
list may do either without hearing REFUSED, which is a
deliberate answer and not an error. The distinction the
module keeps sharp is refuse versus ignore: refusing tells
the asker the door exists and is closed, which is right for
misconfigured clients that would otherwise retry forever,
while dropping silently is reserved for the flood case where
even a refusal is amplification currency. Transfer ACLs get
the stricter default because a zone transfer is the whole
database walking out the door, and the audit exists for the
classic drift: the secondary that was decommissioned two
quarters ago and still holds transfer rights, a door key in
a departed employee's pocket.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Refused


@dataclass
class ZoneAcl:
    zone: str
    query_allow: set[str] = field(default_factory=set)
    transfer_allow: set[str] = field(default_factory=set)
    query_open: bool = True
    refusals: int = 0
    silent_drops: int = 0

    def check_query(
        self, source: str, flooding: bool = False
    ) -> str:
        if self.query_open or source in self.query_allow:
            return f"{source} may query {self.zone}"
        if flooding:
            self.silent_drops += 1
            return (
                f"{source} dropped silently: during a flood "
                "even a refusal is amplification currency"
            )
        self.refusals += 1
        raise Refused(
            f"{source} may not query {self.zone}: REFUSED, a "
            "deliberate answer, so the misconfigured client "
            "stops retrying against a wall it cannot see"
        )

    def check_transfer(self, source: str) -> str:
        if source not in self.transfer_allow:
            self.refusals += 1
            raise Refused(
                f"{source} may not transfer {self.zone}: a "
                "zone transfer is the whole database walking "
                "out the door"
            )
        return f"{source} may transfer {self.zone}"

    def grant_transfer(self, source: str) -> None:
        if source in self.transfer_allow:
            raise Invalid(f"{source} already holds the key")
        self.transfer_allow.add(source)

    def revoke_transfer(self, source: str) -> str:
        if source not in self.transfer_allow:
            raise Invalid(f"{source} holds no key to revoke")
        self.transfer_allow.remove(source)
        return f"{source}'s transfer key revoked"

    def key_audit(
        self, active_secondaries: set[str]
    ) -> list[str]:
        return sorted(
            f"{holder}: holds transfer rights and is not an "
            "active secondary; a door key in a departed "
            "employee's pocket"
            for holder in self.transfer_allow
            if holder not in active_secondaries
        )
