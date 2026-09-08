from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.histogram import Histogram


def latency_histogram() -> Histogram:
    return Histogram(bounds=[10, 50, 100, 500, 1000])


class TestObserve:
    def test_samples_land_in_buckets(self):
        hist = latency_histogram()
        hist.observe(5)  # bucket 0 (<10)
        hist.observe(75)  # bucket 2 (50-100)
        assert hist.total == 2


class TestQuantile:
    def test_the_median_of_a_tight_distribution(self):
        hist = latency_histogram()
        for _ in range(100):
            hist.observe(30)  # all in the 10-50 bucket
        assert hist.quantile(0.5) == 50

    def test_the_tail_lands_in_a_higher_bucket(self):
        hist = latency_histogram()
        for _ in range(95):
            hist.observe(30)
        for _ in range(5):
            hist.observe(700)  # tail in the 500-1000 bucket
        assert hist.quantile(0.99) == 1000

    def test_a_quantile_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            latency_histogram().quantile(1.5)

    def test_an_empty_histogram_has_no_quantile(self):
        with pytest.raises(Invalid):
            latency_histogram().quantile(0.5)


class TestConstruction:
    def test_unordered_bounds_are_refused(self):
        with pytest.raises(Invalid):
            Histogram(bounds=[100, 10, 50])
