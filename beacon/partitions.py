"""Registry partitions: two halves, two truths, one honest merge.

A network partition splits the registry into halves that each
keep accepting registrations, and both halves are right about
what they saw, which is the whole problem. During the split
each side stamps its writes with its own epoch counter, and
the merge afterward is a reconciliation, not a battle: keys
touched on only one side carry over untouched, keys touched
on both sides keep the higher version with the loser recorded
in the merge report, and deletions carry through their
tombstones so the merge cannot resurrect what one side buried.
The report is the artifact that matters, every conflicted key
with both claims and the winner's reason, because the incident
review will ask what the merge decided and "it converged" is
an answer for dashboards, not for the team whose instance
vanished in the reconciliation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class PartitionSide:
    name: str
    entries: dict[str, tuple[str, int]] = field(
        default_factory=dict
    )
    tombstones: dict[str, int] = field(default_factory=dict)

    def write(self, key: str, value: str, version: int) -> None:
        held = self.entries.get(key)
        if held is not None and held[1] >= version:
            raise Invalid(
                f"{key}: {version} does not advance {held[1]}"
            )
        self.entries[key] = (value, version)
        self.tombstones.pop(key, None)

    def delete(self, key: str, version: int) -> None:
        if key not in self.entries:
            raise Invalid(f"{key} is not on side {self.name}")
        self.entries.pop(key)
        self.tombstones[key] = version


def merge_partitions(
    left: PartitionSide, right: PartitionSide
) -> tuple[dict[str, tuple[str, int]], str]:
    merged: dict[str, tuple[str, int]] = {}
    conflicts: list[str] = []
    buried: list[str] = []
    keys = (
        set(left.entries)
        | set(right.entries)
        | set(left.tombstones)
        | set(right.tombstones)
    )
    for key in sorted(keys):
        left_entry = left.entries.get(key)
        right_entry = right.entries.get(key)
        grave = max(
            left.tombstones.get(key, -1),
            right.tombstones.get(key, -1),
        )
        best = None
        winner = ""
        if left_entry and (
            not right_entry or left_entry[1] >= right_entry[1]
        ):
            best, winner = left_entry, left.name
            loser = (
                f"{right.name} held {right_entry[0]}@"
                f"{right_entry[1]}"
                if right_entry
                else ""
            )
        elif right_entry:
            best, winner = right_entry, right.name
            loser = (
                f"{left.name} held {left_entry[0]}@"
                f"{left_entry[1]}"
                if left_entry
                else ""
            )
        if best is not None and grave > best[1]:
            buried.append(
                f"{key}: the tombstone at {grave} outranks "
                f"{best[0]}@{best[1]}; the merge cannot "
                "resurrect what one side buried"
            )
            continue
        if best is None:
            continue
        merged[key] = best
        if left_entry and right_entry and left_entry != right_entry:
            conflicts.append(
                f"{key}: {winner} wins with {best[0]}@"
                f"{best[1]} ({loser}); the loser is recorded "
                "because it-converged is an answer for "
                "dashboards"
            )
    lines = [
        f"{len(merged)} key(s) merged, {len(conflicts)} "
        f"conflict(s), {len(buried)} kept buried"
    ]
    lines.extend(f"  {entry}" for entry in conflicts)
    lines.extend(f"  {entry}" for entry in buried)
    return merged, "\n".join(lines)
