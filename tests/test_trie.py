from __future__ import annotations

from beacon.trie import Trie


def loaded() -> Trie:
    trie = Trie()
    for word in ("api", "app", "apple", "apply", "banana"):
        trie.insert(word)
    return trie


class TestMembership:
    def test_an_inserted_word_is_found(self):
        assert loaded().contains("apple")

    def test_a_prefix_that_is_not_a_word_is_not_a_member(self):
        assert not loaded().contains("ap")

    def test_an_absent_word_is_not_found(self):
        assert not loaded().contains("orange")


class TestPrefix:
    def test_completions_of_a_prefix_are_listed_sorted(self):
        assert loaded().with_prefix("app") == ["app", "apple", "apply"]

    def test_a_prefix_that_is_also_a_word_appears(self):
        assert "app" in loaded().with_prefix("app")

    def test_an_unmatched_prefix_yields_nothing(self):
        assert loaded().with_prefix("xyz") == []

    def test_the_empty_prefix_lists_everything(self):
        assert loaded().with_prefix("") == [
            "api",
            "app",
            "apple",
            "apply",
            "banana",
        ]
