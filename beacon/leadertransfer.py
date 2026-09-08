"""Leadership transfer: hand the lead to a chosen node without waiting out an election timeout.

Sometimes a Raft leader wants to step down deliberately, for a
graceful shutdown, a rebalance, or to move the lead to a better
placed node, and the crude way, simply stopping, forces the
cluster to wait a full election timeout and then hold a possibly
contested election. A directed transfer is cleaner. The leader
first stops accepting new client entries, so the log stops moving,
then brings the chosen successor fully up to date, replicating any
entries it lacks, because a successor whose log is behind could not
win an election and the transfer would fail. Only once the target's
log matches does the leader send it a signal to start an election
immediately, skipping the timeout, and because the target is up to
date and the term is fresh it wins at once while the old leader
steps down. The load-bearing precondition is that the target must
be caught up before the signal is sent, and the module enforces
exactly that: it refuses to transfer to a lagging target, since a
signal to a behind node would trigger an election it cannot win and
leave the cluster leaderless until the timeout it was trying to
avoid.
"""

from __future__ import annotations

from beacon.errors import Refused


def transfer(
    target_last_index: int, leader_last_index: int, accepting_entries: bool
) -> str:
    if accepting_entries:
        raise Refused(
            "the leader is still accepting new entries; it must "
            "stop first so the log stops moving before the target "
            "can be brought fully up to date"
        )
    if target_last_index < leader_last_index:
        raise Refused(
            f"the target is at index {target_last_index} behind the "
            f"leader's {leader_last_index}; signaling a behind node "
            "triggers an election it cannot win and strands the "
            "cluster until the timeout the transfer was avoiding"
        )
    return "send-timeout-now"
