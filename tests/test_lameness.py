from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lameness import LamenessTracker


def tracker() -> LamenessTracker:
    return LamenessTracker()


class TestScoring:
    def test_the_broken_promise_is_named(self):
        chosen = tracker()
        verdict = chosen.observe(
            "eu.example.com.", "ns2", answered_with_authority=False
        )
        assert "the parent's promise, broken by the child" in (
            verdict
        )

    def test_three_shrugs_earn_quarantine(self):
        chosen = tracker()
        for _ in range(2):
            chosen.observe("z.", "ns2", False)
        verdict = chosen.observe("z.", "ns2", False)
        assert "QUARANTINED" in verdict
        assert "consulted last, not never" in verdict

    def test_an_authoritative_answer_resets_the_score(self):
        chosen = tracker()
        chosen.observe("z.", "ns2", False)
        verdict = chosen.observe("z.", "ns2", True)
        assert "servers get fixed" in verdict
        assert not chosen.edges[("z.", "ns2")].quarantined()


class TestConsultationOrder:
    def test_the_healthy_are_asked_first(self):
        chosen = tracker()
        for _ in range(3):
            chosen.observe("z.", "ns-bad", False)
        chosen.observe("z.", "ns-good", True)
        order = chosen.consultation_order(
            "z.", ["ns-bad", "ns-good"]
        )
        assert order == ["ns-good", "ns-bad"]

    def test_no_servers_cannot_be_ordered(self):
        with pytest.raises(Invalid):
            tracker().consultation_order("z.", [])


class TestTheCensus:
    def test_the_census_prices_the_waste(self):
        chosen = tracker()
        chosen.observe("z.", "ns1", True)
        chosen.observe("z.", "ns2", False)
        census = chosen.census("z.")
        assert "1 wasted query(ies) paid to lameness" in census
        assert "ns1: authoritative" in census
        assert "ns2: lame (1)" in census

    def test_the_classic_finding_is_named_when_it_appears(self):
        chosen = tracker()
        chosen.observe("z.", "ns2", True)
        for _ in range(3):
            chosen.observe("z.", "ns2", False)
        census = chosen.census("z.")
        assert "never on the child, the classic" in census

    def test_an_unobserved_zone_has_no_census(self):
        with pytest.raises(Invalid):
            tracker().census("ghost.")
