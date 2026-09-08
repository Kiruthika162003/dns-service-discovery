from __future__ import annotations

import pytest

from beacon.anycast import AnycastFabric
from beacon.errors import Invalid, Missing

CLIENTS = {
    f"c{number}": (
        "eu" if number < 6 else "us" if number < 10 else "asia"
    )
    for number in range(14)
}
REROUTE = {
    client: ("us" if home == "eu" else "eu")
    for client, home in CLIENTS.items()
}


def fabric() -> AnycastFabric:
    built = AnycastFabric()
    for site in ("eu", "us", "asia"):
        built.add_site(site, 10)
    for client, site in CLIENTS.items():
        built.route_client(client, site)
    return built


class TestCatchment:
    def test_load_is_the_catchment_size(self):
        chosen = fabric()
        assert chosen.sites == {"eu": 6, "us": 4, "asia": 4}

    def test_routing_to_a_ghost_site_is_missing(self):
        with pytest.raises(Missing):
            fabric().route_client("cX", "mars")

    def test_a_capacityless_site_cannot_serve(self):
        with pytest.raises(Invalid):
            AnycastFabric().add_site("weak", 0)


class TestWithdrawal:
    def test_the_catchment_reroutes_in_one_event(self):
        chosen = fabric()
        verdict = chosen.withdraw("eu", REROUTE)
        assert "6 client(s) rerouted in one convergence event" in (
            verdict
        )
        assert chosen.sites == {"us": 10, "asia": 4}

    def test_a_blackholed_client_is_refused(self):
        chosen = fabric()
        broken = dict(REROUTE)
        del broken["c0"]
        with pytest.raises(Invalid) as caught:
            chosen.withdraw("eu", broken)
        assert "the network would blackhole it" in str(
            caught.value
        )

    def test_rerouting_to_the_withdrawing_site_is_refused(self):
        chosen = fabric()
        broken = dict(REROUTE)
        broken["c0"] = "eu"
        with pytest.raises(Invalid):
            chosen.withdraw("eu", broken)


class TestTheSurge:
    def test_the_worst_failover_is_named_with_its_load(self):
        report = fabric().surge_report(REROUTE)
        assert "the worst failover is eu -> us at 100%" in report
        assert "untested until it is real" in report
