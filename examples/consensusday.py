"""The consensus day: a vote is won, logs converge, a read is served, and the lead moves on.

Run with: python -m examples.consensusday
"""

from __future__ import annotations

from beacon.commitindex import commit_index
from beacon.jointconsensus import joint_majority
from beacon.leadertransfer import transfer
from beacon.logmatching import append
from beacon.prevote import can_start_election, would_grant_prevote
from beacon.raftvote import Voter
from beacon.readindex import read_index_decision


def morning_the_prevote():
    grants = sum(
        would_grant_prevote(
            peer_has_leader=False,
            candidate_last_index=9,
            candidate_last_term=4,
            peer_last_index=9,
            peer_last_term=4,
        )
        for _ in range(3)
    )
    ok = can_start_election(grants, cluster_size=5)
    print(f"morning  prevote: {grants} grants, election allowed = {ok}")


def midday_the_election():
    voter = Voter(current_term=4)
    granted, term = voter.request_vote(
        candidate_term=5,
        candidate_id="n2",
        candidate_last_index=9,
        candidate_last_term=4,
        my_last_index=9,
        my_last_term=4,
    )
    print(f"midday   vote granted = {granted} in term {term}")


def afternoon_the_logs_converge():
    follower = [1, 1, 2]
    repaired = append(follower, prev_index=2, prev_term=1, entries=[3, 3])
    print(f"afternoon follower log {follower} -> {repaired}")


def commit_the_majority():
    match = [6, 6, 6, 5, 5]
    terms = {6: 5, 5: 2}
    committed = commit_index(match, current_term=5, entry_terms=terms)
    print(f"commit   index advances to {committed} on a majority")


def evening_the_read():
    verdict = read_index_decision(
        commit_index=6, applied_index=6, leadership_confirmed=True
    )
    print(f"evening  linearizable read: {verdict}")


def night_the_membership_change():
    old = {"n1", "n2", "n3"}
    new = {"n3", "n4", "n5"}
    votes = {"n2", "n3", "n4"}
    passed = joint_majority(votes, old, new)
    print(f"night    joint majority across old and new = {passed}")


def handoff_the_lead():
    signal = transfer(
        target_last_index=6, leader_last_index=6, accepting_entries=False
    )
    print(f"handoff  {signal} to a caught-up successor")


def main() -> int:
    morning_the_prevote()
    midday_the_election()
    afternoon_the_logs_converge()
    commit_the_majority()
    evening_the_read()
    night_the_membership_change()
    handoff_the_lead()
    try:
        read_index_decision(6, 6, leadership_confirmed=False)
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
