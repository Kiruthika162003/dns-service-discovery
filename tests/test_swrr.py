from __future__ import annotations

from collections import Counter
from itertools import pairwise

import pytest

from beacon.errors import Invalid
from beacon.swrr import SmoothWeighted


class TestProportions:
    def test_a_cycle_matches_the_weights(self):
        swrr = SmoothWeighted({"a": 5, "b": 1, "c": 1})
        counts = Counter(swrr.cycle())
        assert counts == Counter({"a": 5, "b": 1, "c": 1})

    def test_the_counters_return_to_zero_after_a_cycle(self):
        swrr = SmoothWeighted({"a": 5, "b": 1, "c": 1})
        swrr.cycle()
        assert all(value == 0 for value in swrr.current.values())

    def test_the_pattern_repeats_across_cycles(self):
        swrr = SmoothWeighted({"a": 3, "b": 1})
        first = swrr.cycle()
        second = swrr.cycle()
        assert first == second


class TestSmoothness:
    def test_the_heavy_server_does_not_burst_all_at_once(self):
        swrr = SmoothWeighted({"a": 5, "b": 1, "c": 1})
        sequence = swrr.cycle()
        longest_run = 1
        run = 1
        for prev, cur in pairwise(sequence):
            run = run + 1 if cur == prev else 1
            longest_run = max(longest_run, run)
        assert longest_run < 5


class TestRefusals:
    def test_no_servers_is_refused(self):
        with pytest.raises(Invalid):
            SmoothWeighted({})

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            SmoothWeighted({"a": 0})
