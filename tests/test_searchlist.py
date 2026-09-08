from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.searchlist import SearchList

SUFFIXES = (
    "team.corp.example",
    "corp.example",
    "example",
)


def searchlist() -> SearchList:
    return SearchList(suffixes=SUFFIXES)


class TestExpansion:
    def test_the_shorthand_tours_the_suffixes(self):
        candidates = searchlist().candidates("db")
        assert candidates == [
            "db.team.corp.example",
            "db.corp.example",
            "db.example",
            "db",
        ]

    def test_enough_dots_skip_the_tour_first(self):
        candidates = searchlist().candidates(
            "payments.stripe.com"
        )
        assert candidates[0] == "payments.stripe.com"

    def test_the_trailing_dot_is_absolute_intent(self):
        candidates = searchlist().candidates("db.")
        assert candidates[0] == "db"

    def test_an_empty_list_is_absolute_with_extra_steps(self):
        with pytest.raises(Invalid):
            SearchList(suffixes=())


class TestTheTypoMultiplier:
    def test_a_hit_stops_the_tour_early(self):
        found, tried = searchlist().resolve_against(
            "db", {"db.corp.example"}
        )
        assert found == "db.corp.example"
        assert tried == 2

    def test_the_typo_burns_one_query_per_suffix(self):
        chosen = searchlist()
        found, tried = chosen.resolve_against("bd", set())
        assert found is None
        assert tried == 4
        assert chosen.typo_burns == 4

    def test_the_census_names_the_login_storm(self):
        chosen = searchlist()
        for _ in range(3):
            chosen.resolve_against("bd", set())
        census = chosen.typo_census()
        assert "12 burned" in census
        assert "amplifying one misconfigured hostname" in census


class TestTheShadow:
    def test_the_new_name_that_hijacks_a_shorthand(self):
        collisions = searchlist().shadow_check(
            "db.team.corp.example", shorthands=["db", "web"]
        )
        assert len(collisions) == 1
        assert (
            "db would now resolve to db.team.corp.example "
            "(candidate 1)"
        ) in collisions[0]
        assert "without anyone editing anything" in collisions[0]

    def test_an_unrelated_name_shadows_nobody(self):
        assert searchlist().shadow_check(
            "cache.other.example", shorthands=["db"]
        ) == []
