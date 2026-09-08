from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lsmcompaction import (
    levels_needed,
    read_amplification,
    write_amplification,
)


class TestLevels:
    def test_a_small_dataset_is_one_level(self):
        assert levels_needed(total_size=100, level0_size=100, fanout=10) == 1

    def test_levels_grow_with_the_log_of_the_size(self):
        # 10000 over a 10 L0 at fanout 10 -> log10(1000)=3, +1 = 4
        assert levels_needed(10000, 10, 10) == 4

    def test_a_fanout_below_two_is_refused(self):
        with pytest.raises(Invalid):
            levels_needed(1000, 10, fanout=1)


class TestAmplification:
    def test_write_amplification_scales_with_levels_and_fanout(self):
        assert write_amplification(levels=4, fanout=10) == 40

    def test_read_amplification_is_the_level_count(self):
        assert read_amplification(levels=4) == 4

    def test_more_levels_cost_more_reads(self):
        assert read_amplification(6) > read_amplification(3)

    def test_a_zero_level_read_is_refused(self):
        with pytest.raises(Invalid):
            read_amplification(0)
