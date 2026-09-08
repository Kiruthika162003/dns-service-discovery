"""The hosts file: the override that answers before anyone is asked.

Every resolver ships with a layer older than DNS itself: a
local file of name-to-address pairs consulted before any
query leaves the machine, and its power is exactly its
danger. The override wins silently, which is perfect for
pinning a test box and catastrophic when a two-year-old
entry keeps pointing payments at a decommissioned staging
host, so this layer refuses silence: every hit is stamped
OVERRIDE with the file as the source, and the audit lists
entries by age with the stale suspects first, because a hosts
entry has no TTL, no expiry, and no owner but the person who
forgot writing it. The lint catches the two classic wounds,
the same name mapped twice with the first silently winning,
and the hostname mapped to loopback that explains why the
service works only on its author's laptop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class HostsEntry:
    name: str
    address: str
    added_at: int


@dataclass
class HostsFile:
    entries: list[HostsEntry] = field(default_factory=list)
    override_hits: int = 0

    def add(self, name: str, address: str, now: int) -> None:
        self.entries.append(
            HostsEntry(name=name, address=address, added_at=now)
        )

    def lookup(self, name: str, now: int) -> str | None:
        for entry in self.entries:
            if entry.name == name:
                self.override_hits += 1
                age = now - entry.added_at
                return (
                    f"{entry.address} [OVERRIDE from hosts, "
                    f"{age} tick(s) old]; the file answers "
                    "before anyone is asked"
                )
        return None

    def age_audit(self, now: int, stale_after: int) -> str:
        if stale_after < 1:
            raise Invalid("staleness needs a positive horizon")
        stale = sorted(
            (
                entry
                for entry in self.entries
                if now - entry.added_at >= stale_after
            ),
            key=lambda entry: entry.added_at,
        )
        if not stale:
            return (
                f"{len(self.entries)} entrie(s), none past "
                f"{stale_after}; the file is young enough to "
                "remember its reasons"
            )
        lines = [
            f"{len(stale)} stale suspect(s), oldest first; a "
            "hosts entry has no TTL, no expiry, and no owner "
            "but the person who forgot writing it:"
        ]
        for entry in stale:
            lines.append(
                f"  {entry.name} -> {entry.address} "
                f"({now - entry.added_at} tick(s) old)"
            )
        return "\n".join(lines)

    def lint(self) -> list[str]:
        wounds = []
        seen: dict[str, str] = {}
        for entry in self.entries:
            if entry.name in seen:
                wounds.append(
                    f"{entry.name} mapped twice: "
                    f"{seen[entry.name]} wins silently over "
                    f"{entry.address}, and silent is the wound"
                )
            else:
                seen[entry.name] = entry.address
            if entry.address.startswith("127.") and not (
                entry.name.startswith("localhost")
            ):
                wounds.append(
                    f"{entry.name} -> {entry.address}: mapped "
                    "to loopback, which is why the service "
                    "works only on its author's laptop"
                )
        return wounds
