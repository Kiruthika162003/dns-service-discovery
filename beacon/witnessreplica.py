"""A witness replica: a cheap vote that breaks ties without storing a byte of data.

A cluster needs an odd number of voters to avoid a tied election,
but a full data replica is expensive, three copies of everything to
tolerate one failure. A witness is the cheap third voter. It
participates in elections and commit quorums like any member, so a
two-data-replica cluster plus a witness can reach a majority and
survive one data replica failing, but it stores none of the data,
so it costs almost nothing to run. The line the module keeps sharp
is that a witness adds availability, not durability. Its vote can
form the majority that elects a leader or commits a write, but the
data still lives only on the data replicas, so a majority made of
the witness plus a single surviving data replica can keep the
cluster deciding while that one replica holds the only copy, and if
that replica is then lost the data is gone no matter how many
witnesses voted. The module computes whether a quorum is met
counting the witness as a voter, and reports how many actual data
copies back the decision, so the difference between a vote and a
copy is never blurred.
"""

from __future__ import annotations

from beacon.errors import Invalid


def has_quorum(
    data_replicas_up: int, total_data_replicas: int, witness_up: bool
) -> bool:
    if data_replicas_up > total_data_replicas:
        raise Invalid(
            "more data replicas are up than exist; the count is "
            "inconsistent"
        )
    total_voters = total_data_replicas + 1
    votes = data_replicas_up + (1 if witness_up else 0)
    return votes > total_voters // 2


def data_copies_behind(data_replicas_up: int) -> int:
    return data_replicas_up


def durable(data_replicas_up: int) -> bool:
    return data_replicas_up >= 1
