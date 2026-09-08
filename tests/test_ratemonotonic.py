from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ratemonotonic import liu_layland_bound, priority, schedulable


class TestPriority:
    def test_a_shorter_period_has_higher_priority(self):
        assert priority(10) > priority(50)

    def test_a_nonpositive_period_is_refused(self):
        with pytest.raises(Invalid):
            priority(0)


class TestBound:
    def test_one_task_can_use_the_whole_processor(self):
        assert liu_layland_bound(1) == pytest.approx(1.0)

    def test_the_bound_falls_toward_69_percent(self):
        assert 0.69 < liu_layland_bound(1000) < 0.70


class TestSchedulable:
    def test_utilization_under_the_bound_is_schedulable(self):
        # two tasks: bound ~0.828
        assert schedulable(0.8, n=2)

    def test_utilization_over_the_bound_is_not(self):
        assert not schedulable(0.9, n=2)

    def test_a_negative_utilization_is_refused(self):
        with pytest.raises(Invalid):
            schedulable(-0.1, n=2)
