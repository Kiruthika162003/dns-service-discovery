"""Bailiwick checking: a server may only testify about its own district.

Cache poisoning's oldest door is the helpful liar: a resolver
asks the com servers about example.com and the response
helpfully includes an A record for bank.net, which a naive
cache stores, and now the attacker owns bank.net for everyone
downstream. The bailiwick rule closes the door with a single
question asked of every record in every response: is this
name inside the zone the responding server has authority
over? Records outside the bailiwick are discarded unstored,
whatever they claim, however useful they look, because the
server was never asked to testify about them and volunteered
testimony from the wrong district is the signature of the
attack. The discard log keeps every rejected record with the
bailiwick that rejected it, since a spike of out-of-district
records from one upstream is not noise, it is someone
rattling the door, and the log is how the rattling gets a
timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid
from beacon.names import Name
from beacon.records import Record


@dataclass
class BailiwickFilter:
    accepted: int = 0
    discard_log: list[str] = field(default_factory=list)

    def filter_response(
        self,
        responding_zone: Name,
        records: list[Record],
        now: int,
    ) -> list[Record]:
        if not records:
            raise Invalid(
                "an empty response has nothing to filter; "
                "handle it as a negative, not here"
            )
        kept = []
        for record in records:
            if record.name.is_subdomain_of(responding_zone):
                kept.append(record)
                self.accepted += 1
            else:
                self.discard_log.append(
                    f"[{now}] {record.name.canonical()} "
                    f"{record.rtype} discarded: outside "
                    f"{responding_zone.canonical()}, "
                    "volunteered testimony from the wrong "
                    "district"
                )
        return kept

    def rattling_report(self, window_start: int) -> str:
        recent = [
            entry
            for entry in self.discard_log
            if int(entry.split("]")[0][1:]) >= window_start
        ]
        if not recent:
            return (
                f"{self.accepted} record(s) accepted, no "
                "out-of-district testimony this window; the "
                "door is quiet"
            )
        lines = [
            f"{len(recent)} out-of-district record(s) this "
            "window; someone is rattling the door, and now "
            "the rattling has timestamps:"
        ]
        lines.extend(f"  {entry}" for entry in recent)
        return "\n".join(lines)
