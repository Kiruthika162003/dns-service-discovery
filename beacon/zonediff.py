"""Zone diffs: what changed, what it breaks, and whether the serial noticed.

Two versions of a zone differ in three currencies: records
added, records removed, and records whose value moved, and
the diff names each with its blast estimate, because removing
an A record that something still resolves is an outage filed
in advance. The serial check rides every diff: content that
changed under an unchanged serial is the classic silent
publish, secondaries sleeping through the change because the
number they poll never moved, and the diff refuses to bless
it. The risk ranking is the review tool: CNAME retargets and
deletions sort above additions because additions break only
their author while deletions break their consumers, and the
summary line is written for the change request, three
currencies and a serial verdict, short enough to read and
specific enough to argue with.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid
from beacon.serialmath import newer


@dataclass
class ZoneDiff:
    added: list[str]
    removed: list[str]
    changed: list[str]
    serial_verdict: str

    def risk_ranked(self) -> list[str]:
        return (
            [f"REMOVED {entry}" for entry in self.removed]
            + [f"CHANGED {entry}" for entry in self.changed]
            + [f"added {entry}" for entry in self.added]
        )

    def summary(self) -> str:
        return (
            f"{len(self.added)} added, {len(self.removed)} "
            f"removed, {len(self.changed)} changed; "
            f"{self.serial_verdict}"
        )


def diff_zones(
    old_records: dict[str, str],
    new_records: dict[str, str],
    old_serial: int,
    new_serial: int,
) -> ZoneDiff:
    added = sorted(set(new_records) - set(old_records))
    removed = sorted(set(old_records) - set(new_records))
    changed = sorted(
        key
        for key in set(old_records) & set(new_records)
        if old_records[key] != new_records[key]
    )
    content_moved = bool(added or removed or changed)
    if content_moved and old_serial == new_serial:
        raise Invalid(
            f"content moved under serial {old_serial}: the "
            "classic silent publish, and secondaries sleep "
            "through changes whose number never moved"
        )
    if content_moved:
        if not newer(new_serial, old_serial):
            raise Invalid(
                f"serial went backward: {new_serial} does not "
                f"follow {old_serial}"
            )
        serial_verdict = (
            f"serial advanced {old_serial} -> {new_serial}"
        )
    elif old_serial != new_serial:
        serial_verdict = (
            "serial bumped with no content change; a no-op "
            "publish that wakes every secondary for nothing"
        )
    else:
        serial_verdict = "nothing moved, serial agrees"
    return ZoneDiff(
        added=added,
        removed=removed,
        changed=changed,
        serial_verdict=serial_verdict,
    )


def review_page(diff: ZoneDiff) -> str:
    lines = [diff.summary()]
    for entry in diff.risk_ranked():
        note = ""
        if entry.startswith("REMOVED"):
            note = (
                "; deletions break their consumers, an "
                "outage filed in advance if anything still "
                "resolves it"
            )
        elif entry.startswith("CHANGED"):
            note = "; retargets move traffic that was working"
        lines.append(f"  {entry}{note}")
    return "\n".join(lines)
