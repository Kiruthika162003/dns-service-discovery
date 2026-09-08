from __future__ import annotations

import pytest

from beacon.backoff import (
    capped_exponential,
    decorrelated_jitter,
    full_jitter,
)
from beacon.errors import Invalid


class TestCappedExponential:
    def test_it_doubles_each_attempt(self):
        assert capped_exponential(1.0, 0, 100) == 1.0
        assert capped_exponential(1.0, 3, 100) == 8.0

    def test_it_stops_at_the_cap(self):
        assert capped_exponential(1.0, 20, 100) == 100

    def test_a_nonpositive_base_is_refused(self):
        with pytest.raises(Invalid):
            capped_exponential(0, 1, 100)


class TestFullJitter:
    def test_the_draw_scales_the_ceiling(self):
        # ceiling at attempt 3 is 8; draw 0.5 -> 4
        assert full_jitter(1.0, 3, 100, 0.5) == 4.0

    def test_a_zero_draw_can_retry_immediately(self):
        assert full_jitter(1.0, 3, 100, 0.0) == 0.0

    def test_a_draw_outside_the_unit_interval_is_refused(self):
        with pytest.raises(Invalid):
            full_jitter(1.0, 3, 100, 1.0)


class TestDecorrelatedJitter:
    def test_it_spreads_between_base_and_thrice_previous(self):
        # base 1, previous 10, span = 30 - 1 = 29; draw 0 -> base 1
        assert decorrelated_jitter(1.0, 10.0, 100, 0.0) == 1.0
        # draw approaching 1 -> near base + span = 30
        assert decorrelated_jitter(1.0, 10.0, 100, 0.5) == pytest.approx(
            1.0 + 14.5
        )

    def test_it_respects_the_cap(self):
        assert decorrelated_jitter(1.0, 1000.0, 50, 0.9) == 50

    def test_a_previous_below_base_is_refused(self):
        with pytest.raises(Invalid):
            decorrelated_jitter(5.0, 1.0, 100, 0.5)
