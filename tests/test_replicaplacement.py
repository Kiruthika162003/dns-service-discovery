from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.replicaplacement import domains_covered, place

NODES = {
    "eu-1": "eu",
    "eu-2": "eu",
    "us-1": "us",
    "us-2": "us",
    "ap-1": "ap",
}


class TestDiversity:
    def test_three_replicas_land_in_three_domains(self):
        placement = place("key-1", NODES, replicas=3)
        assert domains_covered(placement, NODES) == 3
        assert len(placement) == 3

    def test_the_placement_is_stable(self):
        assert place("key-1", NODES, 3) == place("key-1", NODES, 3)


class TestForcedDoubling:
    def test_more_replicas_than_domains_doubles_up(self):
        two_zones = {"eu-1": "eu", "eu-2": "eu", "us-1": "us"}
        placement = place("key-1", two_zones, replicas=3)
        assert len(placement) == 3
        # only two domains exist, so one is used twice
        assert domains_covered(placement, two_zones) == 2


class TestRefusals:
    def test_more_replicas_than_nodes_is_refused(self):
        with pytest.raises(Invalid):
            place("key-1", NODES, replicas=10)

    def test_zero_replicas_is_refused(self):
        with pytest.raises(Invalid):
            place("key-1", NODES, replicas=0)
