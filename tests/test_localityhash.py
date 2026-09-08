from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.localityhash import choose, local_fraction

BACKENDS = {
    "eu-1": "eu",
    "eu-2": "eu",
    "us-1": "us",
    "us-2": "us",
}
KEYS = [f"key-{i}" for i in range(3000)]


class TestChoice:
    def test_it_returns_a_known_backend(self):
        assert choose("key-1", BACKENDS, caller_zone="eu") in BACKENDS

    def test_a_negative_bonus_is_refused(self):
        with pytest.raises(Invalid):
            choose("key-1", BACKENDS, caller_zone="eu", bonus=-1)

    def test_no_backends_is_refused(self):
        with pytest.raises(Invalid):
            choose("key-1", {}, caller_zone="eu")


class TestLocality:
    def test_a_strong_bonus_keeps_most_traffic_local(self):
        fraction = local_fraction(KEYS, BACKENDS, caller_zone="eu", bonus=5.0)
        assert fraction > 0.95

    def test_no_bonus_splits_across_zones(self):
        # with bonus 0 it is plain hashing, roughly half local
        fraction = local_fraction(KEYS, BACKENDS, caller_zone="eu", bonus=0.0)
        assert 0.35 < fraction < 0.65

    def test_the_preference_still_allows_spill(self):
        # only remote backends exist; the key must cross zones
        remote_only = {"us-1": "us", "us-2": "us"}
        assert (
            local_fraction(KEYS[:100], remote_only, caller_zone="eu", bonus=5.0)
            == 0.0
        )
