"""Two-phase commit: unanimous prepare then one decision, and its blocking window.

Two-phase commit makes a change atomic across several participants
by splitting it into a vote and a decision. In the first phase the
coordinator asks every participant to prepare, and each either votes
yes, promising it can commit and holding the necessary locks, or
votes no. In the second phase the coordinator decides: commit if
every vote was yes, abort if any was no, and tells everyone. The
atomicity is real, all commit or none does, but the protocol has a
notorious flaw the module makes explicit. A participant that has
voted yes has promised to commit and must hold its locks until it
hears the decision, and if the coordinator crashes after collecting
the yes votes but before broadcasting the decision, that participant
is stuck in doubt: it cannot commit, because maybe someone voted no,
and it cannot abort, because maybe everyone voted yes, so it blocks,
holding locks, until the coordinator returns. This blocking on a
single coordinator failure is why two-phase commit is avoided for
high availability and why three-phase and consensus-based commit
exist. The module computes the decision from the votes and reports a
participant's state, naming the in-doubt block as the cost it is.
"""

from __future__ import annotations

from beacon.errors import Invalid


def decide(votes: list[bool]) -> str:
    if not votes:
        raise Invalid(
            "a commit with no participants has nothing to make "
            "atomic; there is no decision to reach"
        )
    return "commit" if all(votes) else "abort"


def participant_state(voted_yes: bool, decision_received: bool) -> str:
    if not voted_yes:
        return "aborted"
    if decision_received:
        return "committed"
    return "in-doubt-blocked"
