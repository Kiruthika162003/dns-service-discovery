from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.namelimits import check_label, check_name, wire_length


class TestLabel:
    def test_a_normal_label_passes(self):
        assert check_label("example") is None

    def test_a_sixty_three_octet_label_is_the_maximum(self):
        assert check_label("a" * 63) is None

    def test_a_sixty_four_octet_label_is_refused(self):
        with pytest.raises(Invalid) as caught:
            check_label("a" * 64)
        assert "six bits can express" in str(caught.value)

    def test_an_empty_label_is_refused(self):
        with pytest.raises(Invalid):
            check_label("")


class TestWireLength:
    def test_it_counts_length_prefixes_and_the_root(self):
        # www(3)+1, example(7)+1, com(3)+1, +1 root = 17
        assert wire_length(["www", "example", "com"]) == 17


class TestName:
    def test_a_short_name_passes_and_returns_its_size(self):
        assert check_name(["www", "example", "com"]) == 17

    def test_many_short_labels_can_bust_the_limit(self):
        # 127 labels of one octet: 127*2 + 1 = 255, still ok
        labels = ["a"] * 127
        assert check_name(labels) == 255

    def test_one_more_label_exceeds_255(self):
        labels = ["a"] * 128
        with pytest.raises(Invalid) as caught:
            check_name(labels)
        assert "over the 255 limit" in str(caught.value)
