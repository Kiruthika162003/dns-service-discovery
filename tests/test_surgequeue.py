from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.surgequeue import SurgeQueue


class TestConstruction:
    def test_a_zero_concurrency_is_refused(self):
        with pytest.raises(Invalid):
            SurgeQueue(concurrency=0, surge_depth=5)


class TestAdmit:
    def test_it_runs_up_to_the_concurrency(self):
        queue = SurgeQueue(concurrency=2, surge_depth=2)
        assert queue.admit() == "run"
        assert queue.admit() == "run"

    def test_it_queues_a_brief_spike(self):
        queue = SurgeQueue(concurrency=1, surge_depth=2)
        queue.admit()  # run
        assert queue.admit() == "queued"
        assert queue.admit() == "queued"

    def test_it_sheds_a_sustained_overload(self):
        queue = SurgeQueue(concurrency=1, surge_depth=1)
        queue.admit()  # run
        queue.admit()  # queued
        with pytest.raises(Refused) as caught:
            queue.admit()
        assert "shed as prompt rejection" in str(caught.value)


class TestDraining:
    def test_a_completion_lets_a_queued_request_start(self):
        queue = SurgeQueue(concurrency=1, surge_depth=2)
        queue.admit()  # run
        queue.admit()  # queued
        queue.complete()
        queue.start_queued()
        assert queue.active == 1
        assert queue.queued == 0

    def test_completing_nothing_is_refused(self):
        with pytest.raises(Invalid):
            SurgeQueue(1, 1).complete()
