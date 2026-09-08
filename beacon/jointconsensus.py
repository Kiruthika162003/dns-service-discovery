"""Joint consensus: change the cluster's membership through a phase that needs both majorities.

Changing which servers form a Raft cluster is deceptively
dangerous, because if the old configuration and the new one could
each make decisions on their own during the switch, they could
elect two different leaders at the same moment, one by a majority
of the old set and one by a majority of the new, and the cluster
would split. Joint consensus closes that window by making the
transition atomic in the only way that matters for agreement.
Between the old configuration and the new one the cluster enters a
joint configuration in which every decision, an election or a
commit, requires a majority of the old set and a majority of the
new set at the same time, so no decision can be made that both
halves do not endorse, and two disjoint majorities become
impossible. Only once the joint configuration is itself committed
does the cluster move on to the new configuration alone. The module
computes whether a set of votes carries a joint majority, requiring
it to clear both configurations independently, which is the exact
condition that keeps a membership change from ever producing a
split brain.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _is_majority(votes: set[str], config: set[str]) -> bool:
    return len(votes & config) > len(config) // 2


def joint_majority(
    votes: set[str], old_config: set[str], new_config: set[str]
) -> bool:
    if not old_config or not new_config:
        raise Invalid(
            "a joint configuration needs a non-empty old and new "
            "set; a membership change to or from nothing is not a "
            "transition this protects"
        )
    return _is_majority(votes, old_config) and _is_majority(
        votes, new_config
    )


def single_majority(votes: set[str], config: set[str]) -> bool:
    if not config:
        raise Invalid("an empty configuration has no majority")
    return _is_majority(votes, config)
