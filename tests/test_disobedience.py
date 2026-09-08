from __future__ import annotations

import pytest

from beacon.disobedience import PopulationMix
from beacon.errors import Invalid


def mix() -> PopulationMix:
    return PopulationMix(obedient=80, pinned=20, ttl=60)


class TestTheDecay:
    def test_the_failover_instant_holds_everyone(self):
        assert mix().traffic_at_dead_address(0) == 100

    def test_the_obedient_decay_on_schedule(self):
        assert mix().traffic_at_dead_address(30) == 60
        assert mix().traffic_at_dead_address(45) == 40

    def test_past_the_ttl_only_the_floor_remains(self):
        assert mix().traffic_at_dead_address(60) == 20
        assert mix().traffic_at_dead_address(600) == 20

    def test_the_chart_ends_on_the_floor(self):
        chart = mix().chart(ticks=70)
        assert chart[0] == 100
        assert chart[-1] == 20


class TestTheFinding:
    def test_the_floor_is_named_with_its_classroom(self):
        finding = mix().floor_finding()
        assert "20 of 100 client(s) (20%)" in finding
        assert "a floor no DNS change can lower" in finding
        assert "most expensive possible classroom" in finding

    def test_the_obedient_fleet_empties_on_schedule(self):
        clean = PopulationMix(obedient=50, pinned=0, ttl=30)
        assert "empties on schedule" in clean.floor_finding()


class TestRefusals:
    def test_the_empty_population_is_trivial(self):
        with pytest.raises(Invalid):
            PopulationMix(obedient=0, pinned=0, ttl=30)

    def test_time_starts_at_the_failover(self):
        with pytest.raises(Invalid):
            mix().traffic_at_dead_address(-1)
