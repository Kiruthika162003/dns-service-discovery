from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zonespread import SpreadChecker


def checker() -> SpreadChecker:
    built = SpreadChecker()
    built.place("billing", "billing-1", "rack-a")
    built.place("billing", "billing-2", "rack-a")
    built.place("billing", "billing-3", "rack-b")
    built.place("search", "search-1", "rack-a")
    built.place("search", "search-2", "rack-a")
    built.place("search", "search-3", "rack-a")
    return built


class TestTheBlast:
    def test_the_spread_service_survives_its_worst_domain(self):
        domain, lost, survivors = checker().worst_blast(
            "billing"
        )
        assert (domain, lost, survivors) == ("rack-a", 2, 1)
        assert "1 survive and keep serving" in (
            checker().verdict("billing")
        )

    def test_three_in_one_rack_is_one_copy_in_costume(self):
        verdict = checker().verdict("search")
        assert "one copy wearing 3 copies' cost" in verdict
        assert "one power supply away from zero" in verdict

    def test_an_unplaced_service_has_no_blast(self):
        with pytest.raises(Invalid):
            checker().worst_blast("ghost")

    def test_double_placement_is_refused(self):
        built = checker()
        with pytest.raises(Invalid):
            built.place("billing", "billing-1", "rack-c")


class TestTheRebalance:
    def test_the_suggestion_is_a_change_request(self):
        suggestion = checker().rebalance_suggestion("search")
        assert (
            "move search-3 from rack-a to rack-a" not in suggestion
        )
        assert "move search-3 from rack-a" in suggestion
        assert "this is a change request" in suggestion

    def test_a_spread_within_one_moves_nothing(self):
        built = SpreadChecker()
        built.place("api", "api-1", "rack-a")
        built.place("api", "api-2", "rack-b")
        assert "moving anything buys nothing" in (
            built.rebalance_suggestion("api")
        )
