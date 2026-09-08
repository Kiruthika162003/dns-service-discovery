from __future__ import annotations

import pytest

from beacon.countminsketch import CountMinSketch
from beacon.errors import Invalid


class TestNeverUndercount:
    def test_the_estimate_is_at_least_the_true_count(self):
        sketch = CountMinSketch(width=256, depth=4)
        for _ in range(50):
            sketch.add("hot")
        for i in range(500):
            sketch.add(f"cold-{i}")
        assert sketch.estimate("hot") >= 50

    def test_a_heavy_hitter_is_not_hidden(self):
        sketch = CountMinSketch(width=256, depth=4)
        for _ in range(1000):
            sketch.add("heavy")
        sketch.add("light")
        assert sketch.estimate("heavy") > sketch.estimate("light")


class TestConstruction:
    def test_a_zero_dimension_is_refused(self):
        with pytest.raises(Invalid):
            CountMinSketch(width=0, depth=4)

    def test_a_negative_add_is_refused(self):
        with pytest.raises(Invalid) as caught:
            CountMinSketch(16, 4).add("x", count=-1)
        assert "never-undercount" in str(caught.value)


class TestEstimate:
    def test_an_unseen_item_estimates_zero_or_more(self):
        sketch = CountMinSketch(width=1024, depth=5)
        assert sketch.estimate("never-added") >= 0
