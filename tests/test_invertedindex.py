from __future__ import annotations

from beacon.invertedindex import InvertedIndex


def loaded() -> InvertedIndex:
    index = InvertedIndex()
    index.add("svc-1", {"production", "database"})
    index.add("svc-2", {"production", "cache"})
    index.add("svc-3", {"staging", "database"})
    return index


class TestQueries:
    def test_and_intersects_the_posting_lists(self):
        assert loaded().query_and(["production", "database"]) == {"svc-1"}

    def test_or_unions_the_posting_lists(self):
        assert loaded().query_or(["cache", "staging"]) == {"svc-2", "svc-3"}

    def test_a_single_term_returns_its_list(self):
        assert loaded().query_and(["production"]) == {"svc-1", "svc-2"}


class TestEdges:
    def test_an_and_with_an_absent_term_is_empty(self):
        assert loaded().query_and(["production", "nonexistent"]) == set()

    def test_an_or_with_an_absent_term_ignores_it(self):
        assert loaded().query_or(["cache", "nonexistent"]) == {"svc-2"}

    def test_an_empty_and_is_empty(self):
        assert loaded().query_and([]) == set()
