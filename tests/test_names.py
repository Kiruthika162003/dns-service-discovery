from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.names import Name


class TestParsing:
    def test_case_and_trailing_dot_normalize_away(self):
        assert Name.parse("WWW.Example.COM").canonical() == (
            "www.example.com."
        )
        assert Name.parse("www.example.com.").canonical() == (
            "www.example.com."
        )

    def test_the_root_is_a_name_too(self):
        assert Name.parse(".").is_root()
        assert Name.parse(".").canonical() == "."

    def test_double_dots_spell_nothing(self):
        with pytest.raises(Invalid) as caught:
            Name.parse("a..example.com")
        assert "cannot exist" in str(caught.value)

    def test_the_label_length_limit_is_enforced(self):
        with pytest.raises(Invalid):
            Name.parse("x" * 64 + ".com")

    def test_the_whole_name_ceiling_is_enforced(self):
        long_name = ".".join(["a" * 60] * 5)
        with pytest.raises(Invalid) as caught:
            Name.parse(long_name)
        assert "byte ceiling" in str(caught.value)

    def test_non_ascii_is_refused_out_loud(self):
        with pytest.raises(Invalid) as caught:
            Name.parse("café.example.com")
        assert "speaks ascii and says so" in str(caught.value)

    def test_edge_hyphens_are_refused(self):
        with pytest.raises(Invalid):
            Name.parse("-bad.example.com")


class TestAncestry:
    def test_the_parent_chain_walks_to_the_root(self):
        chain = Name.parse("a.b.example.com").ancestry()
        assert [name.canonical() for name in chain] == [
            "a.b.example.com.",
            "b.example.com.",
            "example.com.",
            "com.",
            ".",
        ]

    def test_subdomain_tests_read_from_the_right(self):
        child = Name.parse("api.internal.example.com")
        assert child.is_subdomain_of(Name.parse("example.com"))
        assert not child.is_subdomain_of(Name.parse("ample.com"))

    def test_everything_is_under_the_root(self):
        assert Name.parse("x.y").is_subdomain_of(Name.parse("."))


class TestWildcards:
    def test_the_star_matches_one_or_more_labels(self):
        star = Name.parse("*.example.com")
        assert star.wildcard_matches(Name.parse("a.example.com"))
        assert star.wildcard_matches(
            Name.parse("a.b.example.com")
        )

    def test_the_star_never_matches_the_empty_set(self):
        star = Name.parse("*.example.com")
        assert not star.wildcard_matches(
            Name.parse("example.com")
        )

    def test_only_wildcards_may_match_wildly(self):
        with pytest.raises(Invalid):
            Name.parse("plain.example.com").wildcard_matches(
                Name.parse("a.example.com")
            )
