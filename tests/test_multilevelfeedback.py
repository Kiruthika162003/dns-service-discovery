from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.multilevelfeedback import MultilevelFeedbackQueue


class TestDemotion:
    def test_using_the_full_slice_demotes(self):
        mlfq = MultilevelFeedbackQueue(levels=3)
        assert mlfq.next_level(0, used_full_slice=True) == 1
        assert mlfq.next_level(1, used_full_slice=True) == 2

    def test_yielding_early_stays_high(self):
        mlfq = MultilevelFeedbackQueue(levels=3)
        assert mlfq.next_level(0, used_full_slice=False) == 0

    def test_demotion_stops_at_the_bottom(self):
        mlfq = MultilevelFeedbackQueue(levels=3)
        assert mlfq.next_level(2, used_full_slice=True) == 2


class TestBoost:
    def test_boost_returns_to_the_top(self):
        assert MultilevelFeedbackQueue(3).boost() == 0


class TestConstruction:
    def test_one_level_is_refused(self):
        with pytest.raises(Invalid):
            MultilevelFeedbackQueue(1)

    def test_an_out_of_range_level_is_refused(self):
        with pytest.raises(Invalid):
            MultilevelFeedbackQueue(3).next_level(5, used_full_slice=True)
