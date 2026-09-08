"""Multi-version concurrency control: readers see a snapshot, so they never block writers.

The contention between readers and writers is that a naive store must
either let a reader block a writer, holding a read lock while it
works, or risk the reader seeing a half-applied write. Multi-version
concurrency control removes the contention by never overwriting.
Every write creates a new version of the value, tagged with the
timestamp at which it committed, and old versions are kept, so a read
does not take a lock at all: it names a snapshot timestamp and sees
the latest version that committed at or before that snapshot, a
consistent view of the data as it stood at that instant, regardless
of any writes happening concurrently. Readers never block writers and
writers never block readers, because they touch different versions,
which is an enormous concurrency win for read-heavy workloads. The
cost the module keeps in view is space and cleanup: keeping old
versions consumes storage, and a version becomes garbage only once no
active snapshot could still read it, so a system needs to track the
oldest live snapshot and reclaim versions below it, and a long-running
reader pins old versions alive. The module writes a new version,
reads the visible version for a snapshot, and identifies the versions
reclaimable below the oldest live snapshot.
"""

from __future__ import annotations

from beacon.errors import Invalid


class MVCC:
    def __init__(self) -> None:
        self.versions: dict[str, list[tuple[int, str]]] = {}

    def write(self, key: str, value: str, commit_ts: int) -> None:
        chain = self.versions.setdefault(key, [])
        if chain and commit_ts <= chain[-1][0]:
            raise Invalid(
                f"a write at {commit_ts} is not newer than the last "
                f"version at {chain[-1][0]}; commit timestamps must "
                "increase"
            )
        chain.append((commit_ts, value))

    def read(self, key: str, snapshot_ts: int) -> str | None:
        chain = self.versions.get(key, [])
        visible = None
        for commit_ts, value in chain:
            if commit_ts <= snapshot_ts:
                visible = value
            else:
                break
        return visible

    def reclaimable(self, key: str, oldest_live_snapshot: int) -> int:
        chain = self.versions.get(key, [])
        count = 0
        for index in range(len(chain) - 1):
            next_commit = chain[index + 1][0]
            if next_commit <= oldest_live_snapshot:
                count += 1
            else:
                break
        return count
