from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.weightedhealth import WeightedFleet, health_to_weight


def fleet() -> WeightedFleet:
    built = WeightedFleet()
    built.observe("healthy", 1.0, 100)
    built.observe("degraded", 0.6, 100)
    built.observe("dying", 0.05, 100)
    return built


class TestTheCurve:
    def test_the_healthy_instance_keeps_full_weight(self):
        assert health_to_weight(1.0, 100) == 100

    def test_the_degraded_instance_serves_less(self):
        assert health_to_weight(0.6, 100) == 60

    def test_below_the_floor_the_weight_is_zero(self):
        assert health_to_weight(0.05, 100) == 0

    def test_a_score_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            health_to_weight(1.5, 100)


class TestTheFleet:
    def test_effective_weights_follow_the_curve(self):
        assert fleet().effective_weights() == {
            "healthy": 100,
            "degraded": 60,
            "dying": 0,
        }

    def test_binary_oversends_to_the_degraded(self):
        assert fleet().binary_weights() == {
            "healthy": 100,
            "degraded": 100,
            "dying": 0,
        }

    def test_the_report_states_the_direction_correctly(self):
        report = fleet().capacity_report()
        assert (
            "weighted routing keeps 160 weight unit(s) against "
            "binary's 200"
        ) in report
        assert "binary health oversends" in report

    def test_a_base_weight_below_one_is_refused(self):
        with pytest.raises(Invalid):
            WeightedFleet().observe("x", 1.0, 0)


class TestTheFloor:
    def test_the_dying_instance_is_named_a_corpse(self):
        findings = fleet().floor_report()
        assert len(findings) == 1
        assert "dying at 5% health drops to zero weight" in (
            findings[0]
        )
        assert "keep a corpse warm" in findings[0]

    def test_a_healthy_fleet_names_no_corpses(self):
        clean = WeightedFleet()
        clean.observe("a", 0.9, 100)
        assert clean.floor_report() == []
