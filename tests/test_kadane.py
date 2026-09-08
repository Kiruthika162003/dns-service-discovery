from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.kadane import maximum_subarray


class TestMaximumSubarray:
    def test_the_classic_mixed_sequence(self):
        values = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
        total, start, end = maximum_subarray(values)
        assert total == 6
        assert (start, end) == (3, 6)  # the run [4, -1, 2, 1]

    def test_an_all_positive_sequence_is_taken_whole(self):
        total, start, end = maximum_subarray([1, 2, 3])
        assert total == 6
        assert (start, end) == (0, 2)

    def test_an_all_negative_sequence_returns_the_least_negative(self):
        total, start, end = maximum_subarray([-5, -2, -8])
        assert total == -2
        assert (start, end) == (1, 1)

    def test_a_single_element_is_its_own_answer(self):
        assert maximum_subarray([7]) == (7, 0, 0)

    def test_the_reported_span_sums_to_the_reported_total(self):
        values = [3, -1, 4, -1, 5, -9, 2, 6]
        total, start, end = maximum_subarray(values)
        assert sum(values[start : end + 1]) == total


class TestRefusals:
    def test_an_empty_sequence_is_refused(self):
        with pytest.raises(Invalid):
            maximum_subarray([])
