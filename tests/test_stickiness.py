from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.stickiness import AffinityTable


def table() -> AffinityTable:
    built = AffinityTable()
    for backend in ("b1", "b2", "b3"):
        built.add_backend(backend)
    return built


class TestAffinity:
    def test_the_session_returns_to_its_backend(self):
        chosen = table()
        first = chosen.route("user-7")
        backend = first.split(" -> ")[1].split(" ")[0]
        second = chosen.route("user-7")
        assert f"-> {backend} (affinity held" in second
        assert chosen.honored == 1

    def test_the_session_lives_where_its_state_lives(self):
        chosen = table()
        chosen.route("user-7")
        assert "the session lives where its state lives" in (
            chosen.route("user-7")
        )

    def test_no_healthy_backend_cannot_conjure_a_survivor(self):
        chosen = table()
        for backend in ("b1", "b2", "b3"):
            chosen.mark_down(backend)
        with pytest.raises(Missing):
            chosen.route("user-7")


class TestHealthOutranksAffinity:
    def test_a_dead_backend_releases_its_sessions(self):
        chosen = table()
        first = chosen.route("user-7")
        backend = first.split(" -> ")[1].split(" ")[0]
        verdict = chosen.mark_down(backend)
        assert "released 1 session(s)" in verdict
        assert "serving errors politely" in verdict

    def test_the_released_session_repins_elsewhere(self):
        chosen = table()
        first = chosen.route("user-7")
        backend = first.split(" -> ")[1].split(" ")[0]
        chosen.mark_down(backend)
        second = chosen.route("user-7")
        assert "re-pinned, its backend died" in second
        assert backend not in second.split(" -> ")[1]

    def test_marking_a_healthy_absence_is_refused(self):
        with pytest.raises(Invalid):
            table().mark_down("ghost")


class TestTheLedger:
    def test_the_repins_are_availability_winning(self):
        chosen = table()
        first = chosen.route("user-7")
        backend = first.split(" -> ")[1].split(" ")[0]
        chosen.route("user-7")
        chosen.mark_down(backend)
        chosen.route("user-7")
        ledger = chosen.ledger()
        assert "1 affinity honor(s), 2 re-pin(s)" in ledger
        assert "availability winning exactly when it should" in (
            ledger
        )
