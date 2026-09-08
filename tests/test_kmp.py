from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.kmp import search


class TestSearch:
    def test_it_finds_a_pattern(self):
        assert search("abxabcabcaby", "abcaby") == 6

    def test_it_finds_at_the_start(self):
        assert search("hello world", "hello") == 0

    def test_a_missing_pattern_is_minus_one(self):
        assert search("aaaaa", "aab") == -1

    def test_a_pattern_longer_than_the_text(self):
        assert search("hi", "hello") == -1


class TestSelfOverlap:
    def test_a_pattern_with_repeated_prefix(self):
        # the failure function earns its keep on self-overlapping patterns
        assert search("aaaaaab", "aaab") == 3

    def test_overlapping_first_occurrence(self):
        assert search("abababab", "abab") == 0

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            search("text", "")
