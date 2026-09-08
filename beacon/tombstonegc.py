"""Tombstone GC: keep a delete marker until every replica sees it, or the data comes back.

Deleting a key in a replicated log-structured store is not a
removal but a write: a tombstone, a marker that says this key is
gone, which must propagate to every replica just as an ordinary
write does. The danger is collecting the tombstone too soon. If a
replica was down or partitioned when the delete happened and the
tombstone is garbage-collected before that replica comes back and
syncs, the returning replica still holds the old value, sees no
tombstone to contradict it, and on the next anti-entropy exchange it
pushes the value back to everyone, resurrecting the deleted data,
the notorious bug where deleted records reappear. The defense is a
grace period: a tombstone may be collected only once it is older than
the longest a replica could plausibly be absent, so every replica is
guaranteed to have seen the delete before the evidence of it is
removed. Setting the grace period too short risks resurrection,
setting it too long lets tombstones pile up and bloat the store, so
it is tuned to exceed the maximum realistic replica downtime. The
module decides whether a tombstone is old enough to collect and flags
the resurrection risk of collecting one too early.
"""

from __future__ import annotations

from beacon.errors import Invalid


def may_collect(tombstone_age: int, grace_period: int) -> bool:
    if tombstone_age < 0 or grace_period < 0:
        raise Invalid("an age and a grace period are never negative")
    return tombstone_age >= grace_period


def resurrection_risk_if_collected(
    tombstone_age: int, grace_period: int
) -> bool:
    if tombstone_age < 0 or grace_period < 0:
        raise Invalid("an age and a grace period are never negative")
    return tombstone_age < grace_period
