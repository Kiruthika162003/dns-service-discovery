from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.welford import RunningStats


class TestMean:
    def test_the_running_mean_is_correct(self):
        stats = RunningStats()
        for value in (2, 4, 6, 8):
            stats.add(value)
        assert stats.running_mean() == pytest.approx(5.0)

    def test_no_samples_has_no_mean(self):
        with pytest.raises(Invalid):
            RunningStats().running_mean()


class TestVariance:
    def test_the_sample_variance_is_correct(self):
        stats = RunningStats()
        for value in (2, 4, 6, 8):
            stats.add(value)
        # sample variance of 2,4,6,8 is 20/3
        assert stats.sample_variance() == pytest.approx(20 / 3)

    def test_one_sample_has_no_variance(self):
        stats = RunningStats()
        stats.add(5)
        with pytest.raises(Invalid):
            stats.sample_variance()


class TestStability:
    def test_large_values_small_spread_stay_stable(self):
        stats = RunningStats()
        base = 1_000_000_000
        for value in (base + 1, base + 2, base + 3):
            stats.add(value)
        # true variance is 1.0; the naive sum-of-squares would lose it
        assert stats.sample_variance() == pytest.approx(1.0)
