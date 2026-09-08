from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.watchbudget import HerdPlan


class TestTheTails:
    def test_the_serial_tail_is_the_herd_size(self):
        plan = HerdPlan(
            watchers=1000, batch_size=50, failover_deadline=60
        )
        assert plan.serial_tail() == 1000

    def test_batching_does_not_shrink_the_tail_here(self):
        plan = HerdPlan(
            watchers=1000, batch_size=50, failover_deadline=60
        )
        assert plan.batched_tail() == 1060
        assert plan.batched_tail() > plan.serial_tail()

    def test_the_empty_herd_is_refused(self):
        with pytest.raises(Invalid):
            HerdPlan(
                watchers=0, batch_size=50, failover_deadline=60
            )

    def test_a_zero_batch_notifies_nobody(self):
        with pytest.raises(Invalid):
            HerdPlan(
                watchers=10, batch_size=0, failover_deadline=60
            )


class TestFreshness:
    def test_the_freshness_cost_grows_with_the_window(self):
        small = HerdPlan(
            watchers=1000, batch_size=50, failover_deadline=60
        )
        big = HerdPlan(
            watchers=1000, batch_size=100, failover_deadline=60
        )
        assert small.freshness_cost() == 52
        assert big.freshness_cost() == 102

    def test_the_safe_window_beats_the_deadline(self):
        plan = HerdPlan(
            watchers=1000, batch_size=50, failover_deadline=60
        )
        assert plan.beats_deadline()
        assert "the largest safe window" in plan.plan_report()

    def test_the_greedy_window_misses_the_deadline(self):
        plan = HerdPlan(
            watchers=1000, batch_size=100, failover_deadline=60
        )
        assert not plan.beats_deadline()
        report = plan.plan_report()
        assert "against the reason anyone watches" in report
