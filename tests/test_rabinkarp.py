from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rabinkarp import search


class TestSearch:
    def test_it_finds_a_pattern(self):
        assert search("the quick brown fox", "quick") == 4

    def test_it_finds_at_the_start(self):
        assert search("abcabc", "abc") == 0

    def test_it_finds_at_the_end(self):
        assert search("abcabc", "bc") == 1

    def test_a_missing_pattern_returns_minus_one(self):
        assert search("hello world", "xyz") == -1

    def test_a_pattern_longer_than_the_text_is_absent(self):
        assert search("hi", "hello") == -1

    def test_an_empty_pattern_is_refused(self):
        with pytest.raises(Invalid):
            search("text", "")


class TestCollisionSafety:
    def test_a_hash_match_is_confirmed_by_comparison(self):
        # repeated characters stress the rolling hash; result must be exact
        assert search("aaaaa", "aaa") == 0
        assert search("aaba", "ba") == 2
