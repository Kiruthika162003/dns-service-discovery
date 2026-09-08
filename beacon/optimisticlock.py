"""Optimistic concurrency: no locks, just a version check at commit that aborts on a conflict.

Pessimistic locking assumes conflicts are common and takes a lock
before touching data, blocking anyone else, which is safe but serial.
Optimistic concurrency control makes the opposite bet, that conflicts
are rare, and takes no lock at all. A transaction reads the current
version of the data it cares about, does its work on a private copy,
and at commit time checks whether the version it read is still the
current one. If it is, no one else wrote in the meantime, so the
commit applies and bumps the version. If it is not, someone else
committed a change first, the transaction's work was based on stale
data, and it must abort and retry from the new version rather than
overwrite the intervening write. The bet pays when conflicts are rare,
because transactions run fully concurrently with no blocking, and it
loses when they are common, because the aborts and retries waste the
work of every transaction that lost a race, which is exactly the
regime where pessimistic locking's blocking would have been cheaper.
The module reads a version, commits only when the read version still
matches, bumping it, and refuses a commit against a stale version as
the conflict it is.
"""

from __future__ import annotations

from beacon.errors import Invalid


class OptimisticStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.versions: dict[str, int] = {}

    def read(self, key: str) -> tuple[str | None, int]:
        return self.values.get(key), self.versions.get(key, 0)

    def commit(self, key: str, read_version: int, new_value: str) -> int:
        current = self.versions.get(key, 0)
        if current != read_version:
            raise Invalid(
                f"stale write to {key}: read version {read_version} "
                f"but current is {current}; someone committed first, "
                "so abort and retry from the new version"
            )
        self.values[key] = new_value
        self.versions[key] = current + 1
        return self.versions[key]
