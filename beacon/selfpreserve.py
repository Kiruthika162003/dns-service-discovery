"""Self-preservation: when everyone looks dead at once, suspect the mirror.

Lease expiry assumes failures are independent: one instance
misses its renewals because that instance is sick. But when
forty percent of a fleet misses renewals in one window, the
likelier story is that the registry itself is partitioned from
healthy instances, and evicting them all converts a network
blip into a served outage, the registry amputating a healthy
fleet because it could not hear the heartbeats. The mode
computes its own trigger from the renewal rate: expected
renewals per window come from the registered population, and
when observed renewals fall below the threshold fraction, the
registry stops evicting entirely, serves what it has,
staleness admitted, and says out loud that it distrusts its
own hearing. Exit is by recovery, sustained renewal rate back
above the threshold, never by timeout, because a partition
does not promise to be short and a timer that overrides
evidence is a lie with a clock face.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

THRESHOLD = 0.85


@dataclass
class SelfPreservingRegistry:
    registered: int
    preserving: bool = False
    evictions_suppressed: int = 0
    entered_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.registered < 1:
            raise Invalid("a registry of nobody preserves nothing")

    def expected_renewals(self) -> int:
        return self.registered

    def observe_window(
        self, renewals_seen: int, lapsed: int, now: int
    ) -> str:
        if renewals_seen < 0 or lapsed < 0:
            raise Invalid("counts cannot be negative")
        floor = int(self.expected_renewals() * THRESHOLD)
        if renewals_seen < floor:
            if not self.preserving:
                self.preserving = True
                self.entered_log.append(
                    f"[{now}] entered: {renewals_seen} of "
                    f"{self.expected_renewals()} renewals, "
                    f"floor {floor}"
                )
            self.evictions_suppressed += lapsed
            return (
                f"PRESERVING: {renewals_seen} renewals against "
                f"a floor of {floor}; when everyone looks dead "
                "at once, the registry suspects its own "
                f"hearing and keeps all {lapsed} lapsed "
                "entries, staleness admitted"
            )
        if self.preserving:
            self.preserving = False
            return (
                f"recovered: {renewals_seen} renewals clear "
                f"the floor of {floor}; eviction resumes by "
                "evidence, never by timeout, because a timer "
                "that overrides evidence is a lie with a "
                "clock face"
            )
        return (
            f"normal: {renewals_seen} renewals, {lapsed} "
            "lapsed entries evicted individually"
        )

    def may_evict(self) -> bool:
        return not self.preserving

    def incident_note(self) -> str:
        if not self.entered_log and not self.evictions_suppressed:
            return "self-preservation never fired; leases told the truth all window"
        lines = [
            f"{len(self.entered_log)} preservation episode(s), "
            f"{self.evictions_suppressed} eviction(s) "
            "suppressed"
        ]
        lines.extend(f"  {entry}" for entry in self.entered_log)
        lines.append(
            "the suppressed column is the fleet that a "
            "louder registry would have amputated"
        )
        return "\n".join(lines)
