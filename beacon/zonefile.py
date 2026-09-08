"""The zone file: text becomes authority, and errors arrive with line numbers.

Zones live in files long before they live in servers, and the
parser's duty is to fail the way an editor can act on: every
refusal carries the line number and the reason, because "bad
zone file" sends an operator reading four hundred lines while
"line 17: octet 300 does not fit in a byte" sends them to line
17. The format is deliberately plain: a $ORIGIN line first, an
SOA line second, then one record per line as name, ttl, type,
value, with blank lines and semicolon comments free. Relative
names are completed against the origin and a bare at-sign means
the origin itself, the two conveniences that make hand-written
zones bearable, and both are resolved at parse time so nothing
downstream ever sees a relative name, since half-resolved names
leaking into a running server is how one zone answers for
another by accident.
"""

from __future__ import annotations

from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record, SrvTarget
from beacon.zone import Soa, Zone


def _complete(text: str, origin: Name) -> Name:
    if text == "@":
        return origin
    if text.endswith("."):
        return Name.parse(text)
    return Name.parse(text + "." + origin.canonical())


def _parse_value(
    rtype: str, value_text: str, origin: Name, line_number: int
):
    try:
        if rtype in ("CNAME", "NS"):
            return _complete(value_text, origin)
        if rtype == "TXT":
            return value_text.strip('"').encode("ascii")
        if rtype == "SRV":
            parts = value_text.split()
            if len(parts) != 4:
                raise Invalid(
                    "SRV wants priority weight port target"
                )
            return SrvTarget(
                priority=int(parts[0]),
                weight=int(parts[1]),
                port=int(parts[2]),
                target=_complete(parts[3], origin),
            )
        return value_text
    except Invalid as refusal:
        raise Invalid(
            f"line {line_number}: {refusal}"
        ) from refusal


def parse_zone(text: str) -> Zone:
    origin: Name | None = None
    zone: Zone | None = None
    for line_number, raw in enumerate(
        text.splitlines(), start=1
    ):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("$ORIGIN"):
            if origin is not None:
                raise Invalid(
                    f"line {line_number}: a second $ORIGIN; "
                    "one zone, one origin"
                )
            origin = Name.parse(line.split()[1])
            continue
        if origin is None:
            raise Invalid(
                f"line {line_number}: records before $ORIGIN "
                "have no home; the origin comes first"
            )
        fields = line.split(None, 3)
        if fields[1].upper() == "SOA":
            if zone is not None:
                raise Invalid(
                    f"line {line_number}: a second SOA; one "
                    "zone, one authority"
                )
            numbers = line.split()[2:]
            if len(numbers) != 5 or fields[0] != "@":
                raise Invalid(
                    f"line {line_number}: SOA wants @ SOA "
                    "serial refresh retry expire negative-ttl"
                )
            zone = Zone(
                apex=origin,
                soa=Soa(
                    serial=int(numbers[0]),
                    refresh=int(numbers[1]),
                    retry=int(numbers[2]),
                    expire=int(numbers[3]),
                    negative_ttl=int(numbers[4]),
                ),
            )
            continue
        if zone is None:
            raise Invalid(
                f"line {line_number}: records before the SOA; "
                "authority is declared before it is exercised"
            )
        if len(fields) < 4:
            raise Invalid(
                f"line {line_number}: wants name ttl type value"
            )
        name_text, ttl_text, rtype, value_text = fields
        if not ttl_text.isdigit():
            raise Invalid(
                f"line {line_number}: ttl {ttl_text!r} is not "
                "a number of seconds"
            )
        try:
            record = Record(
                name=_complete(name_text, origin),
                rtype=rtype.upper(),
                value=_parse_value(
                    rtype.upper(), value_text, origin, line_number
                ),
                ttl=int(ttl_text),
            )
            zone.add(record)
        except Invalid as refusal:
            message = str(refusal)
            if not message.startswith("line "):
                message = f"line {line_number}: {message}"
            raise Invalid(message) from refusal
    if zone is None:
        raise Invalid(
            "the file ended without an SOA; text without "
            "authority is notes, not a zone"
        )
    return zone
