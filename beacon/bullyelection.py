"""The bully election: the highest-id live node wins, and it bullies its way back on recovery.

When a leader disappears, the surviving nodes must agree on a new
one, and the bully algorithm settles it by a simple rule: the live
node with the highest id leads. A node that notices the leader is
gone starts an election by messaging every node with a higher id; if
any higher node answers, this node backs off and lets the higher one
carry on, and if none answers, it declares itself the leader and
tells everyone. The name captures the recovery behavior that is both
the point and the drawback. When a previously-failed high-id node
comes back, it immediately starts an election it is bound to win and
bullies the current, perfectly healthy, lower-id leader out of the
role, so the algorithm optimizes for always-highest-leads at the cost
of an election and a leadership change every time a high node
recovers, whether or not one was needed. The module decides an
initiating node's outcome from whether any higher node is alive, and
names the leader of a live set as its maximum id, so the deterministic
winner and the disruptive recovery are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


def election_outcome(candidate_id: int, alive_higher: list[int]) -> str:
    if any(other <= candidate_id for other in alive_higher):
        raise Invalid(
            "the higher-id set contains an id at or below the "
            "candidate; those are not higher nodes"
        )
    return "defer" if alive_higher else "win"


def leader(alive_ids: list[int]) -> int:
    if not alive_ids:
        raise Invalid("an empty set has no node to elect")
    return max(alive_ids)


def disrupts_on_recovery(
    recovering_id: int, current_leader_id: int
) -> bool:
    return recovering_id > current_leader_id
