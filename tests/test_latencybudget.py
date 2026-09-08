from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.latencybudget import ResolutionCost, budget_report


def cost() -> ResolutionCost:
    return ResolutionCost(
        cache_lookup=1,
        network_round_trips=3,
        cname_hops=2,
        validation_checks=4,
    )


class TestTheParts:
    def test_the_parts_are_priced_by_their_weights(self):
        parts = cost().parts()
        assert parts["network"] == 75
        assert parts["cname"] == 40
        assert parts["validation"] == 20
        assert parts["cache"] == 1

    def test_the_total_is_the_sum(self):
        assert cost().total() == 136


class TestTheBudget:
    def test_an_over_budget_resolution_names_the_dominant_line(self):
        report = budget_report(cost(), target=80)
        assert "136 tick(s) against a 80 budget: OVER" in report
        assert "network: 75 (55%)" in report
        assert "the dominant line is network" in report
        assert "a nearer resolver" in report

    def test_a_within_budget_resolution_carries_no_fix(self):
        cheap = ResolutionCost(
            cache_lookup=1,
            network_round_trips=1,
            cname_hops=0,
            validation_checks=1,
        )
        report = budget_report(cheap, target=80)
        assert "within" in report
        assert "the fix is" not in report

    def test_the_lines_sort_biggest_first(self):
        report = budget_report(cost(), target=80)
        lines = report.splitlines()
        assert lines[1].startswith("  network:")
        assert lines[2].startswith("  cname:")

    def test_a_zero_target_is_not_a_budget(self):
        with pytest.raises(Invalid):
            budget_report(cost(), target=0)
