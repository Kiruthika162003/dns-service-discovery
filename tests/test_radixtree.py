from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.radixtree import RadixTree


class TestLongestMatch:
    def test_the_most_specific_prefix_wins(self):
        tree = RadixTree()
        tree.add("10.0.0.0", 8, "broad")
        tree.add("10.1.0.0", 16, "narrow")
        assert tree.longest_match("10.1.2.3") == "narrow"
        assert tree.longest_match("10.2.2.3") == "broad"

    def test_a_default_route_catches_the_rest(self):
        tree = RadixTree()
        tree.add("0.0.0.0", 0, "default")
        tree.add("192.168.0.0", 16, "lan")
        assert tree.longest_match("8.8.8.8") == "default"
        assert tree.longest_match("192.168.1.1") == "lan"

    def test_no_match_returns_none(self):
        tree = RadixTree()
        tree.add("10.0.0.0", 8, "ten")
        assert tree.longest_match("11.0.0.1") is None


class TestRefusals:
    def test_a_prefix_longer_than_the_address_is_refused(self):
        with pytest.raises(Invalid):
            RadixTree().add("10.0.0.0", 40, "x")

    def test_a_bad_address_is_refused(self):
        with pytest.raises(Invalid):
            RadixTree().add("10.0.0", 8, "x")
