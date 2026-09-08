from __future__ import annotations

from beacon.ahocorasick import AhoCorasick


class TestSearch:
    def test_it_finds_all_patterns_in_one_pass(self):
        ac = AhoCorasick(["he", "she", "his", "hers"])
        matches = ac.search("ushers")
        found = {pattern for pattern, _ in matches}
        assert found == {"she", "he", "hers"}

    def test_it_reports_the_end_position(self):
        ac = AhoCorasick(["he", "she", "hers"])
        matches = dict(ac.search("ushers"))
        assert matches["she"] == 3
        assert matches["hers"] == 5

    def test_overlapping_patterns_are_all_caught(self):
        ac = AhoCorasick(["ab", "bc", "abc"])
        found = {pattern for pattern, _ in ac.search("xabcy")}
        assert found == {"ab", "bc", "abc"}

    def test_no_match_returns_empty(self):
        assert AhoCorasick(["zzz"]).search("abcdef") == []

    def test_a_repeated_pattern_matches_each_occurrence(self):
        ac = AhoCorasick(["aa"])
        positions = [i for _, i in ac.search("aaaa")]
        assert positions == [1, 2, 3]


class TestConstruction:
    def test_empty_patterns_are_skipped(self):
        ac = AhoCorasick(["", "ab"])
        assert {p for p, _ in ac.search("zab")} == {"ab"}
