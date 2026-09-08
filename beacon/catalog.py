"""The versioned catalog: watchers ask what changed, not what exists.

A thousand clients polling the full service list every second
is a registry answering the same megabyte over and over; the
catalog fixes it with a version counter that increments on
every mutation and a change log addressed by version. A
watcher says "I have seen through version 40" and receives
only what happened since, which is usually nothing, and
nothing is cheap. The log is a window like every journal in
distributed systems: a watcher that reports a version older
than the window's start cannot be caught up by deltas and is
told to resync with a full snapshot, told loudly, because
applying a partial delta stream to a stale view builds a
catalog that never existed at any version, the distributed
equivalent of a chimera. The bandwidth ledger prices the
design against full polling, since the whole apparatus exists
to make that one number small.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Lagging

LOG_WINDOW = 16
FULL_LIST_COST = 100
DELTA_COST = 4


@dataclass
class Change:
    version: int
    action: str
    service: str
    instance: str


@dataclass
class VersionedCatalog:
    version: int = 0
    entries: dict[str, set[str]] = field(default_factory=dict)
    log: list[Change] = field(default_factory=list)
    delta_bytes: int = 0
    snapshot_bytes: int = 0

    def _record(
        self, action: str, service: str, instance: str
    ) -> None:
        self.version += 1
        self.log.append(
            Change(
                version=self.version,
                action=action,
                service=service,
                instance=instance,
            )
        )
        if len(self.log) > LOG_WINDOW:
            self.log.pop(0)

    def register(self, service: str, instance: str) -> int:
        held = self.entries.setdefault(service, set())
        if instance in held:
            raise Invalid(
                f"{instance} is already in {service}; a "
                "repeat registration is not a change and "
                "minting a version for it would wake every "
                "watcher for nothing"
            )
        held.add(instance)
        self._record("add", service, instance)
        return self.version

    def deregister(self, service: str, instance: str) -> int:
        held = self.entries.get(service, set())
        if instance not in held:
            raise Invalid(
                f"{instance} is not in {service}"
            )
        held.remove(instance)
        self._record("remove", service, instance)
        return self.version

    def watch(self, seen_version: int) -> list[Change]:
        if seen_version > self.version:
            raise Invalid(
                f"seen {seen_version} but the catalog is at "
                f"{self.version}; nobody has seen the future"
            )
        if seen_version == self.version:
            return []
        oldest_available = (
            self.log[0].version if self.log else self.version + 1
        )
        if seen_version < oldest_available - 1:
            raise Lagging(
                f"version {seen_version} predates the log "
                f"window (starts at {oldest_available}); "
                "resync with a snapshot, because deltas onto "
                "a stale view build a catalog that never "
                "existed at any version"
            )
        changes = [
            change
            for change in self.log
            if change.version > seen_version
        ]
        self.delta_bytes += len(changes) * DELTA_COST
        return changes

    def snapshot(self) -> tuple[int, dict[str, set[str]]]:
        self.snapshot_bytes += FULL_LIST_COST
        return self.version, {
            service: set(instances)
            for service, instances in self.entries.items()
        }

    def bandwidth_ledger(self, polls_replaced: int) -> str:
        if polls_replaced < 1:
            raise Invalid("a comparison needs polls to replace")
        polling_cost = polls_replaced * FULL_LIST_COST
        actual = self.delta_bytes + self.snapshot_bytes
        return (
            f"watching cost {actual} byte-unit(s) where "
            f"polling costs {polling_cost}; the whole "
            "apparatus exists to make this number small"
        )
