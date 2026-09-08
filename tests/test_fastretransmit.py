from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.fastretransmit import (
    is_duplicate,
    should_fast_retransmit,
    tolerates_reordering,
)


class TestDuplicate:
    def test_a_repeated_ack_is_a_duplicate(self):
        assert is_duplicate(previous_ack=100, new_ack=100)

    def test_an_advancing_ack_is_not(self):
        assert not is_duplicate(previous_ack=100, new_ack=140)


class TestThreshold:
    def test_three_duplicates_trigger_a_retransmit(self):
        assert should_fast_retransmit(duplicate_count=3)

    def test_fewer_do_not(self):
        assert not should_fast_retransmit(duplicate_count=2)

    def test_a_zero_threshold_is_refused(self):
        with pytest.raises(Invalid):
            should_fast_retransmit(1, threshold=0)


class TestReordering:
    def test_one_or_two_duplicates_are_tolerated_as_reordering(self):
        assert tolerates_reordering(1)
        assert tolerates_reordering(2)

    def test_three_is_treated_as_loss(self):
        assert not tolerates_reordering(3)
