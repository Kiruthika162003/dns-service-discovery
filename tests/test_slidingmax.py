from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.slidingmax import SlidingMax


class TestMaximum:
    def test_it_tracks_the_window_max(self):
        sm = SlidingMax(window=3)
        maxima = []
        for index, value in enumerate([1, 3, 2, 5, 1, 1]):
            sm.push(index, value)
            maxima.append(sm.maximum())
        # windows: [1],[1,3],[1,3,2],[3,2,5],[2,5,1],[5,1,1]
        assert maxima == [1, 3, 3, 5, 5, 5]

    def test_an_aged_max_falls_out_of_the_window(self):
        sm = SlidingMax(window=2)
        sm.push(0, 9)
        sm.push(1, 1)
        # window is now [9,1], max 9
        assert sm.maximum() == 9
        sm.push(2, 1)
        # window [1,1], the 9 aged out
        assert sm.maximum() == 1


class TestRefusals:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            SlidingMax(0)

    def test_a_maximum_before_any_push_is_refused(self):
        with pytest.raises(Invalid):
            SlidingMax(3).maximum()
