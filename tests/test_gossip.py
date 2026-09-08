from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.gossip import MemberView


def view() -> MemberView:
    built = MemberView(owner="node-a")
    for member in ("node-a", "node-b", "node-c"):
        built.join(member)
    return built


class TestSuspicion:
    def test_a_missed_probe_is_never_a_death_sentence(self):
        chosen = view()
        verdict = chosen.probe_missed("node-b", now=10)
        assert "never a death sentence" in verdict
        assert chosen.beliefs["node-b"].state == "suspected"

    def test_the_deadline_declares_death_unrefuted(self):
        chosen = view()
        chosen.probe_missed("node-b", now=10)
        assert chosen.sweep(now=14) == []
        declared = chosen.sweep(now=15)
        assert len(declared) == 1
        assert "expired unrefuted" in declared[0]

    def test_double_suspicion_does_not_reset_the_clock(self):
        chosen = view()
        chosen.probe_missed("node-b", now=10)
        chosen.probe_missed("node-b", now=14)
        assert chosen.sweep(now=15) != []

    def test_strangers_cannot_be_probed(self):
        with pytest.raises(Missing):
            view().probe_missed("node-z", now=0)

    def test_joining_twice_is_refused(self):
        chosen = view()
        with pytest.raises(Invalid):
            chosen.join("node-b")


class TestRefutation:
    def test_the_obituary_is_answered_with_a_new_incarnation(self):
        chosen = view()
        chosen.probe_missed("node-a", now=10)
        incarnation, verdict = chosen.refute_own_death()
        assert incarnation == 1
        assert "newer testimony beats older" in verdict
        assert chosen.beliefs["node-a"].state == "alive"

    def test_the_refutation_overrules_the_rumor_elsewhere(self):
        other = MemberView(owner="node-b")
        other.join("node-b")
        other.join("node-a")
        other.receive_gossip("node-a", "suspected", 0, now=10)
        verdict = other.receive_gossip("node-a", "alive", 1, now=12)
        assert "newer incarnation 1 overrules" in verdict
        assert other.beliefs["node-a"].state == "alive"


class TestGossipMerging:
    def test_stale_rumors_are_discarded_by_incarnation(self):
        chosen = view()
        chosen.receive_gossip("node-b", "alive", 3, now=5)
        verdict = chosen.receive_gossip(
            "node-b", "dead", 1, now=6
        )
        assert "stale rumor" in verdict
        assert chosen.beliefs["node-b"].state == "alive"

    def test_same_incarnation_graver_news_wins(self):
        chosen = view()
        verdict = chosen.receive_gossip(
            "node-b", "suspected", 0, now=5
        )
        assert "graver news wins" in verdict
        calm = chosen.receive_gossip("node-b", "alive", 0, now=6)
        assert calm == "node-b: nothing new"

    def test_rumors_introduce_strangers(self):
        chosen = view()
        verdict = chosen.receive_gossip(
            "node-z", "alive", 0, now=5
        )
        assert "learned of via rumor" in verdict


class TestTheRoster:
    def test_the_roster_counts_the_three_states(self):
        chosen = view()
        chosen.probe_missed("node-b", now=0)
        chosen.probe_missed("node-c", now=0)
        chosen.sweep(now=5)
        assert chosen.roster() == (
            "node-a sees 1 alive, 0 suspected, 2 dead; 0 "
            "obituary(ies) refuted"
        )
