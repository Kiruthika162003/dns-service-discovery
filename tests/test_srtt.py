from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.srtt import Selector


def selector() -> Selector:
    built = Selector()
    for name in ("ns-east", "ns-west"):
        built.add(name)
    return built


class TestSelection:
    def test_the_lowest_estimate_is_chosen(self):
        chosen = selector()
        chosen.observe("ns-east", 20.0)
        chosen.observe("ns-west", 90.0)
        assert chosen.choose() == "ns-east"

    def test_one_slow_answer_nudges_rather_than_slanders(self):
        chosen = selector()
        chosen.observe("ns-east", 20.0)
        chosen.observe("ns-east", 200.0)
        assert chosen.upstreams["ns-east"].srtt < 110

    def test_an_empty_selector_has_nobody(self):
        with pytest.raises(Missing):
            Selector().choose()


class TestTimeouts:
    def test_the_timeout_is_punished_as_a_multiple(self):
        chosen = selector()
        verdict = chosen.observe("ns-east", None)
        assert "entered as 600" in verdict
        assert "told nothing" in verdict
        assert chosen.upstreams["ns-east"].srtt > 200

    def test_negative_round_trips_break_physics(self):
        with pytest.raises(Invalid):
            selector().observe("ns-east", -1.0)


class TestTheRetrial:
    def test_the_disgraced_decay_back_into_rotation(self):
        chosen = selector()
        chosen.observe("ns-west", None)
        assert chosen.choose() == "ns-east"
        for _ in range(60):
            chosen.observe("ns-east", 70.0)
        assert chosen.choose() == "ns-west"
        assert chosen.retrials_granted >= 1

    def test_a_genuinely_fast_incumbent_keeps_the_crown(self):
        chosen = selector()
        chosen.observe("ns-west", None)
        for _ in range(60):
            chosen.observe("ns-east", 55.0)
        assert chosen.choose() == "ns-east"
        assert chosen.upstreams["ns-west"].srtt > 60

    def test_the_standings_read_fastest_first(self):
        chosen = selector()
        chosen.observe("ns-east", 20.0)
        chosen.observe("ns-west", 90.0)
        standings = chosen.standings()
        lines = standings.splitlines()
        assert lines[1].startswith("  ns-east:")
        assert "even the disgraced get asked again" in standings
