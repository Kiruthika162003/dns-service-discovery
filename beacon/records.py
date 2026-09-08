"""Resource records: typed values with a lifespan, validated at creation.

A record is a name, a type, a value, and a TTL, and the value's
grammar depends entirely on the type: an A record carries a
dotted quad whose octets actually fit in a byte, an AAAA
carries colon-grouped hex, a CNAME or NS carries another name,
an SRV carries priority, weight, port, and target, and a TXT
carries bytes the protocol refuses to interpret. Validation
happens at construction because a malformed record discovered
at answer time has already been replicated, cached, and served,
while one refused at creation cost nobody anything. The TTL is
data, not configuration: it rides with the record, zero is
legal and means do-not-cache, and the type keeps no clock of
its own, since whose clock a TTL counts against is the cache's
question, not the record's.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid
from beacon.names import Name

RECORD_TYPES = ("A", "AAAA", "CNAME", "NS", "TXT", "SRV", "SOA")
MAX_TTL = 604_800


def _check_ipv4(value: str) -> None:
    octets = value.split(".")
    if len(octets) != 4:
        raise Invalid(
            f"{value!r} is not a dotted quad; four octets or "
            "it is not an address"
        )
    for octet in octets:
        if not octet.isdigit() or not 0 <= int(octet) <= 255:
            raise Invalid(
                f"octet {octet!r} does not fit in a byte"
            )
        if len(octet) > 1 and octet.startswith("0"):
            raise Invalid(
                f"octet {octet!r} has a leading zero, which "
                "half the world parses as octal"
            )


def _check_ipv6(value: str) -> None:
    if "::" in value:
        halves = value.split("::")
        if len(halves) > 2:
            raise Invalid(
                f"{value!r} compresses twice; one gap only"
            )
        groups = [
            group
            for half in halves
            for group in half.split(":")
            if group
        ]
        if len(groups) >= 8:
            raise Invalid(
                f"{value!r} compresses nothing; the gap must "
                "stand for at least one group"
            )
    else:
        groups = value.split(":")
        if len(groups) != 8:
            raise Invalid(
                f"{value!r} has {len(groups)} group(s); eight "
                "or a compression"
            )
    for group in groups:
        if not 1 <= len(group) <= 4 or any(
            ch not in "0123456789abcdef" for ch in group.lower()
        ):
            raise Invalid(f"group {group!r} is not hex")


@dataclass(frozen=True)
class SrvTarget:
    priority: int
    weight: int
    port: int
    target: Name

    def __post_init__(self) -> None:
        for field_name, value in (
            ("priority", self.priority),
            ("weight", self.weight),
        ):
            if not 0 <= value <= 65_535:
                raise Invalid(
                    f"{field_name} {value} does not fit in "
                    "sixteen bits"
                )
        if not 1 <= self.port <= 65_535:
            raise Invalid(f"port {self.port} is not a port")


@dataclass(frozen=True)
class Record:
    name: Name
    rtype: str
    value: object
    ttl: int

    def __post_init__(self) -> None:
        if self.rtype not in RECORD_TYPES:
            raise Invalid(
                f"{self.rtype} is not a type this beacon "
                f"speaks; it knows {', '.join(RECORD_TYPES)}"
            )
        if not 0 <= self.ttl <= MAX_TTL:
            raise Invalid(
                f"ttl {self.ttl} is outside 0..{MAX_TTL}; zero "
                "means do-not-cache and a week is the ceiling"
            )
        self._check_value()

    def _check_value(self) -> None:
        if self.rtype == "A":
            if not isinstance(self.value, str):
                raise Invalid("A records carry dotted quads")
            _check_ipv4(self.value)
        elif self.rtype == "AAAA":
            if not isinstance(self.value, str):
                raise Invalid("AAAA records carry hex groups")
            _check_ipv6(self.value)
        elif self.rtype in ("CNAME", "NS"):
            if not isinstance(self.value, Name):
                raise Invalid(
                    f"{self.rtype} records point at names, "
                    "not strings; parse first"
                )
        elif self.rtype == "SRV":
            if not isinstance(self.value, SrvTarget):
                raise Invalid("SRV records carry SrvTarget")
        elif self.rtype == "TXT":
            if not isinstance(self.value, bytes):
                raise Invalid(
                    "TXT records carry bytes the protocol "
                    "refuses to interpret"
                )

    def describe(self) -> str:
        if isinstance(self.value, Name):
            shown = self.value.canonical()
        elif isinstance(self.value, SrvTarget):
            shown = (
                f"{self.value.priority} {self.value.weight} "
                f"{self.value.port} "
                f"{self.value.target.canonical()}"
            )
        elif isinstance(self.value, bytes):
            shown = self.value.decode("ascii", "replace")
        else:
            shown = str(self.value)
        return (
            f"{self.name.canonical()} {self.ttl} "
            f"{self.rtype} {shown}"
        )
