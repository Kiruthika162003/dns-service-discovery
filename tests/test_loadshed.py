from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.loadshed import LoadShedder


class TestConstruction:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            LoadShedder(0)


class TestGradient:
    def test_low_priority_sheds_first(self):
        shedder = LoadShedder(capacity=100)
        # 30 in flight: below normal (50) and above low (20)
        assert not shedder.admit(30, "low")
        assert shedder.admit(30, "normal")
        assert shedder.admit(30, "critical")

    def test_critical_survives_almost_to_the_ceiling(self):
        shedder = LoadShedder(capacity=100)
        assert shedder.admit(90, "critical")
        assert not shedder.admit(90, "high")

    def test_nothing_is_admitted_at_full_capacity(self):
        shedder = LoadShedder(capacity=100)
        assert not shedder.admit(100, "critical")


class TestShedOrder:
    def test_the_shed_order_grows_as_load_climbs(self):
        shedder = LoadShedder(capacity=100)
        assert shedder.shed_order(10) == []
        assert shedder.shed_order(30) == ["low"]
        assert shedder.shed_order(60) == ["low", "normal"]
        assert shedder.shed_order(90) == ["low", "normal", "high"]

    def test_an_unknown_priority_is_refused(self):
        with pytest.raises(Invalid):
            LoadShedder(100).cutoff("whenever")
