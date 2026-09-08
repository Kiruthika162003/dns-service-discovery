"""Log compaction: snapshot a log grown too large, and ship it to a lagging peer.

A replicated log that only ever grows would eventually fill the
disk and make restarts glacial as the whole history replays, so a
node compacts: past a size threshold it takes a snapshot of the
state machine up to some index and discards the log entries that
led there, since the snapshot already captures their effect. That
compaction creates a new problem the module names. Once the entries
before the snapshot are gone, a follower that has fallen behind the
snapshot point cannot be caught up by sending it log entries,
because the entries it is missing no longer exist anywhere, so the
leader must ship the entire snapshot instead, the same fallback as a
zone transfer that drops IXFR for AXFR when the journal no longer
covers the gap. A follower merely behind the current log but still
ahead of the snapshot can be caught up the cheap way with ordinary
appends. The module decides when a log warrants a snapshot and, for
a given follower, whether an incremental append suffices or a full
snapshot install is required because the follower trails the
compaction point.
"""

from __future__ import annotations

from beacon.errors import Invalid


def should_snapshot(log_size: int, threshold: int) -> bool:
    if threshold < 1:
        raise Invalid(
            "a snapshot threshold below one would compact on every "
            "entry, which is churn, not compaction"
        )
    return log_size >= threshold


def catch_up_plan(
    follower_next_index: int, snapshot_last_index: int
) -> str:
    if follower_next_index < 1:
        raise Invalid("a next index is at least one")
    if follower_next_index <= snapshot_last_index:
        return "install-snapshot"
    return "append-entries"
