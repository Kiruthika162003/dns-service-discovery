"""ReadIndex: a linearizable read without writing to the log, once leadership is confirmed.

A Raft leader could serve a read by appending a no-op entry and
waiting for it to commit, which is correct but pays a full log
write and replication round for a read that changes nothing.
ReadIndex is the cheaper path to the same linearizable guarantee.
The leader records its current commit index as the read index, then
confirms it is still the leader by exchanging one round of
heartbeats and hearing back from a majority, which rules out the
possibility that a newer leader has already committed something this
one has not seen. Having confirmed leadership, it waits until its
own state machine has applied entries up to the read index, so the
read reflects everything committed as of the moment the read began,
and then serves. Two conditions are therefore load-bearing and the
module makes both explicit: leadership must be freshly confirmed,
because a partitioned old leader serving from a stale commit index
would return data a newer leader has already superseded, and the
applied index must have caught up to the read index, because
serving before the state machine has applied those entries would
read stale state. The module returns wait or serve, and refuses to
serve on unconfirmed leadership.
"""

from __future__ import annotations

from beacon.errors import Refused


def read_index_decision(
    commit_index: int, applied_index: int, leadership_confirmed: bool
) -> str:
    if not leadership_confirmed:
        raise Refused(
            "leadership is not freshly confirmed; a partitioned "
            "old leader serving from a stale commit index would "
            "return data a newer leader has superseded"
        )
    if applied_index < commit_index:
        return "wait"
    return "serve"
