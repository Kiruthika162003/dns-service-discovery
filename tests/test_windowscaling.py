from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.windowscaling import max_window, scaled_window, shift_for


class TestScaledWindow:
    def test_a_shift_multiplies_the_window(self):
        assert scaled_window(1000, shift=7) == 1000 * 128

    def test_a_zero_shift_is_the_raw_field(self):
        assert scaled_window(65535, shift=0) == 65535

    def test_a_shift_over_the_maximum_is_refused(self):
        with pytest.raises(Invalid):
            scaled_window(1000, shift=15)


class TestMaxWindow:
    def test_the_maximum_grows_with_the_shift(self):
        assert max_window(0) == 65535
        assert max_window(14) == 65535 << 14


class TestShiftFor:
    def test_a_small_bdp_needs_no_shift(self):
        assert shift_for(50000) == 0

    def test_a_large_bdp_needs_a_shift(self):
        # 1.25 MB needs the window past 64KB
        assert shift_for(1_250_000) >= 5

    def test_the_smallest_covering_shift_is_chosen(self):
        bdp = 65535 << 3
        assert shift_for(bdp) == 3
