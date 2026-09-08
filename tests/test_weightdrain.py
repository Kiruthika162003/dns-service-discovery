from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.weightdrain import DrainPlan, rampup_schedule


def plan() -> DrainPlan:
    return DrainPlan(instance="web-1", start_weight=100, steps=5)


class TestTheSchedule:
    def test_the_weight_steps_down_to_zero(self):
        assert plan().schedule() == [80, 60, 40, 20, 0]

    def test_a_zero_weight_instance_is_already_drained(self):
        with pytest.raises(Invalid):
            DrainPlan(instance="x", start_weight=0, steps=5)

    def test_a_zero_step_drain_is_a_yank(self):
        with pytest.raises(Invalid) as caught:
            DrainPlan(instance="x", start_weight=10, steps=0)
        assert "the yank it replaces" in str(caught.value)


class TestThePeerShift:
    def test_the_shift_is_bounded_and_reported(self):
        assert plan().largest_peer_shift(4) == 5

    def test_fewer_peers_absorb_a_bigger_shift(self):
        assert plan().largest_peer_shift(1) == 20

    def test_traffic_must_shift_onto_someone(self):
        with pytest.raises(Invalid):
            plan().largest_peer_shift(0)

    def test_the_report_names_the_number_that_matters(self):
        report = plan().drain_report(4)
        assert "largest single-step shift any of 4 peer(s)" in (
            report
        )
        assert "absorbs is 5" in report
        assert "just a slower yank" in report


class TestTheRampUp:
    def test_the_arrival_ramps_from_zero_to_target(self):
        assert rampup_schedule(100, 5) == [20, 40, 60, 80, 100]

    def test_a_ramp_needs_a_target_and_steps(self):
        with pytest.raises(Invalid):
            rampup_schedule(0, 5)
