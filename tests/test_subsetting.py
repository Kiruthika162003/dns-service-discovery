from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.subsetting import SubsetPlan

BACKENDS = tuple(f"backend-{number:02}" for number in range(20))


def plan() -> SubsetPlan:
    return SubsetPlan(backends=BACKENDS, subset_size=4)


class TestDeterminism:
    def test_the_subset_is_stable_across_restarts(self):
        assert plan().stable_across_restarts("client-0")
        assert plan().subset_for("client-0") == [
            "backend-02",
            "backend-07",
            "backend-13",
            "backend-17",
        ]

    def test_neighbors_see_different_worlds(self):
        overlap = plan().neighbor_overlap(
            "client-0", "client-1"
        )
        assert overlap == 1


class TestCoverage:
    def test_fifty_clients_cover_every_backend(self):
        clients = [f"client-{number}" for number in range(50)]
        report = plan().coverage_report(clients)
        assert "heaviest backend seen by 14, lightest by 6" in (
            report
        )
        assert "every backend is in someone's subset" in report

    def test_three_clients_starve_nine_backends(self):
        clients = [f"client-{number}" for number in range(3)]
        report = plan().coverage_report(clients)
        assert report.splitlines()[1].startswith("  STARVED:")
        assert report.count("backend-") >= 9
        assert "their peers drown while they idle" in report


class TestRefusals:
    def test_an_empty_subset_serves_nothing(self):
        with pytest.raises(Invalid):
            SubsetPlan(backends=BACKENDS, subset_size=0)

    def test_the_whole_list_wearing_a_smaller_name(self):
        with pytest.raises(Invalid) as caught:
            SubsetPlan(backends=("a", "b"), subset_size=3)
        assert "wearing a smaller name" in str(caught.value)

    def test_coverage_needs_clients(self):
        with pytest.raises(Invalid):
            plan().coverage_report([])
