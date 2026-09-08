from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.typosquat import SquatWatch, edit_distance


class TestEditDistance:
    def test_the_distances_are_exact(self):
        assert edit_distance("google", "google") == 0
        assert edit_distance("google", "googel") == 2
        assert edit_distance("google", "googe") == 1
        assert edit_distance("google", "gogle") == 1

    def test_insertion_deletion_substitution_all_count(self):
        assert edit_distance("cat", "cats") == 1
        assert edit_distance("cat", "at") == 1
        assert edit_distance("cat", "bat") == 1


class TestTheWatch:
    def test_a_keystroke_away_name_is_a_suspect(self):
        watch = SquatWatch(protected="paypal")
        suspect = watch.edit_suspect("paypa")
        assert suspect is not None
        assert "belongs to someone with a reason" in suspect

    def test_the_far_name_is_no_suspect(self):
        assert (
            SquatWatch(protected="paypal").edit_suspect(
                "microsoft"
            )
            is None
        )

    def test_the_identical_name_is_not_a_typo_of_itself(self):
        assert (
            SquatWatch(protected="paypal").edit_suspect("paypal")
            is None
        )

    def test_an_empty_protected_name_is_refused(self):
        with pytest.raises(Invalid):
            SquatWatch(protected="")


class TestHomoglyphs:
    def test_the_cyrillic_lookalike_is_caught(self):
        watch = SquatWatch(protected="paypal")
        swapped = "p" + chr(0x0430) + "ypal"
        suspect = watch.homoglyph_suspect(swapped)
        assert suspect is not None
        assert "zero to the eye, one to the machine" in suspect

    def test_a_plain_name_is_no_homoglyph(self):
        assert (
            SquatWatch(protected="paypal").homoglyph_suspect(
                "paypal"
            )
            is None
        )


class TestTheScreen:
    def test_the_screen_separates_the_two_kinds(self):
        watch = SquatWatch(protected="paypal")
        report = watch.screen(
            ["paypa", "p" + chr(0x0430) + "ypal", "amazon"]
        )
        assert "2 suspect(s) near paypal" in report
        assert "HOMOGLYPH" in report
        assert "TYPO" in report
        assert "the human decides" in report

    def test_a_clean_neighborhood_says_so(self):
        report = SquatWatch(protected="paypal").screen(
            ["amazon", "google"]
        )
        assert "the neighborhood is clean this pass" in report
