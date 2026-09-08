from __future__ import annotations

import pytest

from beacon.earliestdeadline import next_task, schedulable
from beacon.errors import Invalid


class TestNextTask:
    def test_the_nearest_deadline_runs(self):
        tasks = [("a", 50), ("b", 20), ("c", 40)]
        assert next_task(tasks) == "b"

    def test_a_tie_breaks_deterministically(self):
        assert next_task([("b", 10), ("a", 10)]) == "a"

    def test_no_ready_task_is_refused(self):
        with pytest.raises(Invalid):
            next_task([])


class TestSchedulable:
    def test_full_utilization_is_schedulable(self):
        assert schedulable(1.0)

    def test_over_one_is_not(self):
        assert not schedulable(1.2)

    def test_a_negative_utilization_is_refused(self):
        with pytest.raises(Invalid):
            schedulable(-0.1)
