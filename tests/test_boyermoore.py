from __future__ import annotations

import pytest

from beacon.boyermoore import search
from beacon.errors import Invalid


class TestSearch:
    def test_it_finds_a_pattern(self):
        assert search("the quick brown fox", "brown") == 10

    def test_it_finds_at_the_start(self):
        assert search("abcdef", "abc") == 0

    def test_it_finds_at_the_end(self):
        assert search("abcdef", "def") == 3

    def test_a_missing_pattern_is_minus_one(self):
        assert search("abcdef", "xyz") == -1

    def test_a_pattern_longer_than_text_is_absent(self):
        assert search("hi", "hello") == -1


class TestSkips:
    def test_repeated_alphabet_still_correct(self):
        # a long text where the last char rarely matches -> big skips
        text = "a" * 50 + "needle" + "a" * 50
        assert search(text, "needle") == 50

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            search("text", "")
