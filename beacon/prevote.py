"""Pre-vote: check you could win before bumping the term and disrupting a healthy leader.

A partitioned Raft node keeps timing out and incrementing its term
while it cannot reach anyone, and when the partition heals it
rejoins carrying a term far above everyone else's. Under plain
Raft that high term forces the healthy leader to step down, even
though nothing was wrong with it, and the cluster suffers an
election it did not need just because one node was off sulking with
an inflated term. Pre-vote prevents the disruption by adding a dry
run. Before a node increments its term and becomes a real
candidate, it asks the peers a hypothetical: would you grant me a
vote in the next term, given my log. Crucially this asks without
raising anyone's term, so a node that could not win, because its
log is behind or because the peers still hear from a healthy
leader, learns so cheaply and stands down without ever disturbing
the term. Only if a majority say they would vote does the node
proceed to a real election. The module decides a single pre-vote
grant from the log currency and whether the peer still has a
leader, and tallies whether a real election may start.
"""

from __future__ import annotations

from beacon.errors import Invalid


def would_grant_prevote(
    peer_has_leader: bool,
    candidate_last_index: int,
    candidate_last_term: int,
    peer_last_index: int,
    peer_last_term: int,
) -> bool:
    if peer_has_leader:
        return False
    return candidate_last_term > peer_last_term or (
        candidate_last_term == peer_last_term
        and candidate_last_index >= peer_last_index
    )


def can_start_election(prevotes_granted: int, cluster_size: int) -> bool:
    if cluster_size < 1:
        raise Invalid("a cluster needs at least one member to elect from")
    majority = cluster_size // 2 + 1
    return prevotes_granted >= majority
