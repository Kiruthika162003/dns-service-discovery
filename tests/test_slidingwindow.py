from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.slidingwindow import (
    boundary_burst,
    fixed_window_allows,
    sliding_allows,
    sliding_estimate,
)


class TestFixedWindow:
    def test_it_allows_up_to_the_limit(self):
        assert fixed_window_allows(99, 100)
        assert not fixed_window_allows(100, 100)


class TestSlidingEstimate:
    def test_early_in_the_window_the_previous_count_weighs_heavily(
        self,
    ):
        # 10% into the window, 90% of the previous 100 still counts
        assert sliding_estimate(100, 0, 0.1) == pytest.approx(90.0)

    def test_late_in_the_window_the_previous_count_fades(self):
        assert sliding_estimate(100, 20, 0.9) == pytest.approx(30.0)

    def test_a_fraction_outside_zero_to_one_is_refused(self):
        with pytest.raises(Invalid):
            sliding_estimate(100, 0, 1.5)


class TestTheBurstIsRefused:
    def test_the_fixed_window_would_admit_the_boundary_burst(self):
        # early in the new window the fixed count is only 50, under the limit
        assert fixed_window_allows(50, 100)

    def test_the_sliding_window_refuses_it(self):
        # 100 sent last window, 50 already this window, only 10% in:
        # estimate = 100*0.9 + 50 = 140, over the limit
        assert not sliding_allows(
            previous_count=100,
            current_count=50,
            elapsed_fraction=0.1,
            limit=100,
        )

    def test_the_burst_message_names_the_doubling(self):
        assert "200 inside" in boundary_burst(100)
