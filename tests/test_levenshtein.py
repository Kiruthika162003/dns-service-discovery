from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.levenshtein import distance, within


class TestDistance:
    def test_identical_strings_are_zero_apart(self):
        assert distance("example", "example") == 0

    def test_one_substitution(self):
        assert distance("example", "exumple") == 1

    def test_one_insertion(self):
        assert distance("exmple", "example") == 1

    def test_the_classic_kitten_sitting(self):
        assert distance("kitten", "sitting") == 3

    def test_against_an_empty_string(self):
        assert distance("abc", "") == 3


class TestWithin:
    def test_a_close_typo_is_within_bound(self):
        assert within("paypal", "paypai", bound=1)

    def test_a_distant_string_is_not(self):
        assert not within("paypal", "google", bound=2)

    def test_a_negative_bound_is_refused(self):
        with pytest.raises(Invalid):
            within("a", "b", bound=-1)
