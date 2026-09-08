"""Write-ahead logging: record the intent before the change, so a crash replays to consistency.

A registry that updated its data structures in place and then
crashed mid-update would come back with a half-applied change and no
way to tell, so durable stores write ahead: before touching the
actual data, they append a record of the intended change to a log
that is flushed to stable storage first. If a crash happens the log
is the source of truth, and recovery replays the records that were
logged but not yet reflected in the data, redoing them to reach a
consistent state, so a change is durable the moment its log record is
flushed, before the data itself is updated. The cost the module keeps
in view is write amplification: every change is written twice, once
to the log and once to the data, which is why real systems batch many
log records into one flush, group commit, to amortize the cost. Once
the data is safely persisted up to some point, a checkpoint, the log
before that point is no longer needed for recovery and can be
truncated to bound its growth. The module appends records, tracks how
far the data has been applied, returns the unapplied tail to replay
on recovery, and truncates the log at a checkpoint.
"""

from __future__ import annotations

from beacon.errors import Invalid


class WriteAheadLog:
    def __init__(self) -> None:
        self.records: list[str] = []
        self.applied = 0

    def append(self, record: str) -> int:
        self.records.append(record)
        return len(self.records)

    def apply_up_to(self, index: int) -> None:
        if not 0 <= index <= len(self.records):
            raise Invalid(
                f"cannot apply to index {index}; the log holds "
                f"{len(self.records)} records"
            )
        if index < self.applied:
            raise Invalid(
                "the applied point cannot move backward; the data is "
                "already persisted past there"
            )
        self.applied = index

    def replay(self) -> list[str]:
        return self.records[self.applied :]

    def checkpoint(self) -> None:
        self.records = self.records[self.applied :]
        self.applied = 0
