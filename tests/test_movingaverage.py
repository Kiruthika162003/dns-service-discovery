from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.movingaverage import MovingAverage


class TestAverage:
    def test_it_averages_within_the_window(self):
        ma = MovingAverage(window=3)
        ma.add(3)
        ma.add(6)
        assert ma.average() == pytest.approx(4.5)

    def test_the_oldest_falls_off_the_window(self):
        ma = MovingAverage(window=3)
        for value in (1, 2, 3):
            ma.add(value)
        assert ma.average() == pytest.approx(2.0)
        ma.add(4)  # 1 falls off, window is 2,3,4
        assert ma.average() == pytest.approx(3.0)

    def test_it_lags_a_step_change(self):
        ma = MovingAverage(window=4)
        for _ in range(4):
            ma.add(0)
        ma.add(100)  # a jump, but three zeros still in the window
        assert ma.average() == pytest.approx(25.0)


class TestConstruction:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            MovingAverage(0)

    def test_an_average_before_any_sample_is_refused(self):
        with pytest.raises(Invalid):
            MovingAverage(3).average()
