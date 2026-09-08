from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.readpreference import select


def replicas(primary_up: bool = True) -> list[dict]:
    return [
        {"id": "p", "role": "primary", "healthy": primary_up, "latency": 50},
        {"id": "s1", "role": "secondary", "healthy": True, "latency": 10},
        {"id": "s2", "role": "secondary", "healthy": True, "latency": 30},
    ]


class TestPrimary:
    def test_primary_reads_the_primary(self):
        assert select("primary", replicas()) == "p"

    def test_primary_fails_when_down(self):
        with pytest.raises(Refused):
            select("primary", replicas(primary_up=False))


class TestPreferred:
    def test_primary_preferred_falls_back_to_secondary(self):
        assert select("primary-preferred", replicas(primary_up=False)) == "s1"

    def test_secondary_preferred_uses_a_secondary_first(self):
        assert select("secondary-preferred", replicas()) == "s1"


class TestNearest:
    def test_nearest_picks_the_lowest_latency_healthy(self):
        assert select("nearest", replicas()) == "s1"

    def test_an_unknown_preference_is_refused(self):
        with pytest.raises(Refused):
            select("whatever", replicas())
