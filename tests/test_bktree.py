from __future__ import annotations

import pytest

from beacon.bktree import BKTree
from beacon.errors import Invalid


def loaded() -> BKTree:
    tree = BKTree()
    for word in ("book", "books", "boo", "cook", "cake", "cape", "boon"):
        tree.add(word)
    return tree


class TestSearch:
    def test_it_finds_words_within_the_radius(self):
        result = loaded().search("book", radius=1)
        assert "book" in result
        assert "books" in result
        assert "boo" in result
        assert "boon" in result
        assert "cook" in result

    def test_it_excludes_words_beyond_the_radius(self):
        result = loaded().search("book", radius=1)
        assert "cake" not in result

    def test_an_exact_match_at_radius_zero(self):
        assert loaded().search("cake", radius=0) == ["cake"]

    def test_an_empty_tree_finds_nothing(self):
        assert BKTree().search("anything", radius=2) == []


class TestRefusals:
    def test_a_negative_radius_is_refused(self):
        with pytest.raises(Invalid):
            loaded().search("book", radius=-1)

    def test_a_duplicate_add_is_ignored(self):
        tree = BKTree()
        tree.add("book")
        tree.add("book")
        assert tree.search("book", radius=0) == ["book"]
