from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.morriscounter import MorrisCounter


class TestIncrement:
    def test_a_low_draw_bumps_the_exponent(self):
        counter = MorrisCounter()
        counter.increment(draw=0.0)  # 0 < 2^0 = 1, always bumps first
        assert counter.exponent == 1

    def test_the_probability_halves_as_the_exponent_grows(self):
        counter = MorrisCounter()
        counter.increment(draw=0.0)  # exponent 1, prob now 0.5
        # a draw of 0.7 exceeds 0.5, so no bump
        counter.increment(draw=0.7)
        assert counter.exponent == 1
        # a draw of 0.3 is below 0.5, so it bumps
        counter.increment(draw=0.3)
        assert counter.exponent == 2

    def test_a_draw_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            MorrisCounter().increment(draw=1.0)


class TestEstimate:
    def test_the_estimate_is_two_to_the_exponent_minus_one(self):
        counter = MorrisCounter()
        assert counter.estimate() == 0
        counter.increment(0.0)
        assert counter.estimate() == 1
        counter.increment(0.0)
        assert counter.estimate() == 3
