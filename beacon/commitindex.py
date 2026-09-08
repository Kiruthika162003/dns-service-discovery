"""Commit index: an entry is committed once a majority holds it, and only in the current term.

A replicated log advances by a leader deciding which entries are
safe to apply, and safe means durable against the loss of a
minority of nodes, so an entry is committed only once a majority of
the cluster has it. The leader knows how far each follower's log
matches its own, and the commit index is the highest log position
present on a majority of those match points, including the leader's
own. There is a subtlety that a naive majority count gets wrong and
that costs correctness, the Raft rule that a leader may not commit
an entry from an earlier term merely because it now sits on a
majority, because a later leader could still overwrite it; only an
entry from the leader's current term may be committed on the
strength of its own replication, and earlier entries ride to safety
behind it. The module computes the commit index as the highest
position replicated on a majority whose entry belongs to the
current term, which honors both the durability rule and the term
rule, and refuses a match-index list that does not include the
leader, since a commit decision without the leader's own log is
missing the one replica guaranteed to hold every entry.
"""

from __future__ import annotations

from beacon.errors import Invalid


def commit_index(
    match_indices: list[int],
    current_term: int,
    entry_terms: dict[int, int],
) -> int:
    if not match_indices:
        raise Invalid(
            "the match-index list is empty; it must include at "
            "least the leader's own log, the one replica holding "
            "every entry"
        )
    total = len(match_indices)
    majority = total // 2 + 1
    committed = 0
    for candidate in set(match_indices):
        if candidate <= 0:
            continue
        replicated = sum(1 for m in match_indices if m >= candidate)
        if (
            replicated >= majority
            and entry_terms.get(candidate) == current_term
        ):
            committed = max(committed, candidate)
    return committed
