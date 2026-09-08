"""SVCB and HTTPS records: connection parameters delivered before the connection.

Before SVCB the client learned a name's address, dialed it,
negotiated TLS, and only then discovered which protocols the
endpoint spoke, so HTTP/3 over QUIC needed a wasteful HTTP/1
round trip just to be told to upgrade. RFC 9460 moves that
knowledge into the resolution: an HTTPS record carries the ALPN
list, an alternate port, and address hints, so the client can
open the right connection on the first try. The record has two
modes the module keeps strictly apart. AliasMode, priority zero,
is a same-owner redirect to another target and carries no
parameters, and the rule is that a priority-zero record must
stand alone, because an alias that shares its name with service
records is a fork in the road with no sign. ServiceMode,
priority above zero, carries the parameters and is chosen by
ascending priority with ties broken by weight, so the record
set is a preference list, not a menu the client is free to
reorder.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass(frozen=True)
class SvcbRecord:
    priority: int
    target: str
    params: dict[str, str] = field(default_factory=dict)
    weight: int = 1

    def __post_init__(self) -> None:
        if self.priority < 0:
            raise Invalid("an SVCB priority is never negative")
        if self.is_alias() and self.params:
            raise Invalid(
                "a priority-zero AliasMode record carries no "
                "parameters; it is a redirect, not a service "
                "description"
            )
        if not self.is_alias() and self.target == ".":
            raise Invalid(
                "a ServiceMode target of '.' means the owner "
                "name itself and is only legal in AliasMode"
            )

    def is_alias(self) -> bool:
        return self.priority == 0


@dataclass
class SvcbSet:
    owner: str
    records: list[SvcbRecord]

    def __post_init__(self) -> None:
        aliases = [r for r in self.records if r.is_alias()]
        if aliases and len(self.records) > 1:
            raise Invalid(
                "a priority-zero AliasMode record must stand "
                "alone; mixing it with service records is a "
                "fork in the road with no sign"
            )

    def is_alias_form(self) -> bool:
        return len(self.records) == 1 and self.records[0].is_alias()

    def alias_target(self) -> str:
        if not self.is_alias_form():
            raise Invalid(
                f"{self.owner} is a ServiceMode set and has no "
                "single alias target to follow"
            )
        return self.records[0].target

    def ordered(self) -> list[SvcbRecord]:
        if self.is_alias_form():
            raise Invalid(
                "an AliasMode set is not a preference list; "
                "follow its target instead of ordering it"
            )
        return sorted(
            self.records, key=lambda r: (r.priority, -r.weight)
        )

    def first_choice(self) -> SvcbRecord:
        return self.ordered()[0]

    def supports_h3(self) -> bool:
        for record in self.records:
            alpn = record.params.get("alpn", "")
            if "h3" in alpn.split(","):
                return True
        return False
