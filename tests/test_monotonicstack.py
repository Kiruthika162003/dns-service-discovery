from __future__ import annotations

from beacon.monotonicstack import next_greater


class TestNextGreater:
    def test_it_finds_the_next_greater_value(self):
        # 2 -> 5, 5 -> 7, 3 -> 7, 7 -> none, 1 -> none
        assert next_greater([2, 5, 3, 7, 1]) == [5, 7, 7, -1, -1]

    def test_a_descending_sequence_has_no_greater(self):
        assert next_greater([5, 4, 3, 2]) == [-1, -1, -1, -1]

    def test_an_ascending_sequence_chains_forward(self):
        assert next_greater([1, 2, 3, 4]) == [2, 3, 4, -1]

    def test_equal_values_are_not_strictly_greater(self):
        assert next_greater([3, 3, 5]) == [5, 5, -1]

    def test_an_empty_sequence(self):
        assert next_greater([]) == []
