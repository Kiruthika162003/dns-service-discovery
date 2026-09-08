from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.twoq import TwoQ


class TestConstruction:
    def test_a_zero_size_is_refused(self):
        with pytest.raises(Invalid):
            TwoQ(probation=0, main=4)


class TestPromotion:
    def test_a_new_key_enters_probation(self):
        cache = TwoQ(probation=4, main=4)
        cache.access("a")
        assert "a" in cache.resident()

    def test_a_reaccessed_key_promotes_to_main(self):
        cache = TwoQ(probation=4, main=4)
        cache.access("a")
        cache.access("a")  # proven, promoted
        assert "a" in cache.main


class TestScanResistance:
    def test_a_scan_passes_through_without_evicting_the_hot_main(self):
        cache = TwoQ(probation=2, main=3)
        # build a hot set in main
        for hot in ("h1", "h2", "h3"):
            cache.access(hot)
            cache.access(hot)  # promote each
        assert {"h1", "h2", "h3"} <= cache.resident()
        # a scan of one-time keys flows through the small probation FIFO
        for cold in ("s1", "s2", "s3", "s4", "s5"):
            cache.access(cold)
        # the hot main survives the scan
        assert {"h1", "h2", "h3"} <= cache.resident()

    def test_the_probation_fifo_is_bounded(self):
        cache = TwoQ(probation=2, main=4)
        for key in ("a", "b", "c"):
            cache.access(key)
        # probation holds at most two; the oldest fell off
        assert len(cache.probation) <= 2
