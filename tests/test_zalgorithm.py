from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zalgorithm import search, z_array


class TestZArray:
    def test_the_first_entry_is_the_whole_length(self):
        assert z_array("aabxaab")[0] == 7

    def test_a_repeated_prefix_is_measured(self):
        # "aaa": position 1 matches the prefix for 2 chars, position 2 for 1
        assert z_array("aaa") == [3, 2, 1]

    def test_the_empty_string_has_an_empty_array(self):
        assert z_array("") == []


class TestSearch:
    def test_a_single_occurrence_is_found(self):
        assert search("abxabcabcaby", "abcaby") == [6]

    def test_overlapping_occurrences_are_all_found(self):
        assert search("aaaa", "aa") == [0, 1, 2]

    def test_a_missing_pattern_yields_no_matches(self):
        assert search("abcdef", "xyz") == []

    def test_the_empty_pattern_matches_every_position(self):
        assert search("abc", "") == [0, 1, 2, 3]


class TestRefusals:
    def test_a_reserved_separator_in_the_text_is_refused(self):
        with pytest.raises(Invalid):
            search("ab\x00cd", "cd")
