from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.geoip import GeoRouter


def router() -> GeoRouter:
    built = GeoRouter()
    for region in ("eu-west", "eu-central", "us-east"):
        built.add_region(region)
    built.set_distance("eu-west", "eu-central", 1)
    built.set_distance("eu-west", "us-east", 8)
    built.set_distance("eu-central", "us-east", 7)
    built.locate("203.0.113.5", "eu-west")
    built.locate("8.8.8.8", "us-east")
    return built


class TestRouting:
    def test_the_nearest_healthy_region_answers(self):
        verdict = router().route("203.0.113.5")
        assert "-> eu-west (0 hops by table, confident)" in (
            verdict
        )

    def test_an_unlocated_client_is_a_coin_toss(self):
        with pytest.raises(Missing) as caught:
            router().route("198.51.100.9")
        assert "coin toss with extra steps" in str(caught.value)

    def test_negative_distances_are_refused(self):
        with pytest.raises(Invalid):
            router().set_distance("a", "b", -1)


class TestHonesty:
    def test_the_public_resolver_is_low_confidence(self):
        verdict = router().route("8.8.8.8")
        assert "low confidence" in verdict
        assert "not the user's" in verdict


class TestFallback:
    def test_the_dead_region_yields_the_next_nearest(self):
        chosen = router()
        chosen.mark_down("eu-west")
        verdict = chosen.route("203.0.113.5")
        assert "-> eu-central (1 hops by table" in verdict

    def test_the_down_message_names_the_priority(self):
        verdict = router().mark_down("eu-west")
        assert "proximity to an outage" in verdict

    def test_marking_a_healthy_absence_is_refused(self):
        with pytest.raises(Invalid):
            router().mark_down("mars")
