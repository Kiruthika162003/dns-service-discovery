from __future__ import annotations

import pytest

from beacon.adaptivetimeout import adaptive_timeout, percentile
from beacon.errors import Invalid


class TestPercentile:
    def test_the_median_of_a_simple_set(self):
        assert percentile([10, 20, 30, 40, 50], 0.5) == 30

    def test_the_top_of_the_distribution(self):
        assert percentile([10, 20, 30, 40, 50], 1.0) == 50

    def test_an_empty_sample_is_refused(self):
        with pytest.raises(Invalid):
            percentile([], 0.5)


class TestTimeout:
    def test_the_timeout_sits_above_the_typical_latency(self):
        samples = [100] * 99 + [200]
        chosen = adaptive_timeout(samples, 0.99, 1.5)
        assert chosen > percentile(samples, 0.5)
        assert chosen == percentile(samples, 0.99) * 1.5

    def test_it_tracks_a_faster_service_downward(self):
        fast = adaptive_timeout([10] * 100, 0.99, 1.5)
        slow = adaptive_timeout([1000] * 100, 0.99, 1.5)
        assert fast < slow

    def test_a_floor_is_respected(self):
        assert adaptive_timeout([1, 1, 1], 0.99, 1.5, floor=50) == 50

    def test_a_margin_below_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            adaptive_timeout([10, 20], margin=0.9)
        assert "under the very percentile" in str(caught.value)
