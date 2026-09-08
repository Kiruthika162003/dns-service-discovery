from __future__ import annotations

import pytest

from beacon.checkpointing import overhead_fraction, replay_work
from beacon.errors import Invalid


class TestReplayWork:
    def test_a_longer_interval_means_more_replay(self):
        assert replay_work(checkpoint_interval=60, write_rate=100) == 6000
        assert replay_work(120, 100) > replay_work(60, 100)

    def test_a_nonpositive_interval_is_refused(self):
        with pytest.raises(Invalid):
            replay_work(0, 100)


class TestOverhead:
    def test_frequent_checkpoints_cost_more_overhead(self):
        frequent = overhead_fraction(checkpoint_cost=5, checkpoint_interval=10)
        rare = overhead_fraction(checkpoint_cost=5, checkpoint_interval=100)
        assert frequent > rare

    def test_the_overhead_is_cost_over_interval(self):
        assert overhead_fraction(5, 10) == 0.5

    def test_a_nonpositive_interval_is_refused(self):
        with pytest.raises(Invalid):
            overhead_fraction(5, 0)
