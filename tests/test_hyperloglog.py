from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.hyperloglog import HyperLogLog


class TestEstimate:
    def test_it_estimates_a_large_cardinality_closely(self):
        hll = HyperLogLog(precision=12)
        for i in range(20000):
            hll.add(f"client-{i}")
        estimate = hll.estimate()
        assert abs(estimate - 20000) / 20000 < 0.05

    def test_duplicates_do_not_inflate_the_count(self):
        hll = HyperLogLog(precision=12)
        for _ in range(5000):
            hll.add("same-client")
        assert hll.estimate() < 5

    def test_a_small_cardinality_is_close(self):
        hll = HyperLogLog(precision=12)
        for i in range(100):
            hll.add(f"c-{i}")
        assert abs(hll.estimate() - 100) / 100 < 0.1


class TestConstruction:
    def test_a_precision_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            HyperLogLog(precision=2)
        with pytest.raises(Invalid):
            HyperLogLog(precision=20)
