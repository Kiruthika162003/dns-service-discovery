from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.notify import Notifier, staleness_bought


def notifier() -> Notifier:
    return Notifier(secondaries=("ns2", "ns3"))


class TestTapping:
    def test_the_first_publish_taps_everyone(self):
        chosen = notifier()
        sent = chosen.publish(101, now=0)
        assert sent == [
            "tap ns2: serial 101",
            "tap ns3: serial 101",
        ]
        assert chosen.taps_sent == 2

    def test_the_burst_is_absorbed_into_standing_taps(self):
        chosen = notifier()
        chosen.publish(101, now=0)
        sent = chosen.publish(102, now=1)
        assert all("absorbed" in line for line in sent)
        assert chosen.duplicates_absorbed == 2
        assert chosen.pending["ns2"].serial == 102

    def test_an_empty_tower_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Notifier(secondaries=())
        assert "bell in an empty tower" in str(caught.value)


class TestAcknowledgement:
    def test_catching_up_releases_the_tap(self):
        chosen = notifier()
        chosen.publish(101, now=0)
        verdict = chosen.acknowledge("ns2", 101)
        assert "tap released" in verdict
        assert "ns2" not in chosen.pending

    def test_a_climbed_tap_stands_through_a_stale_ack(self):
        chosen = notifier()
        chosen.publish(101, now=0)
        chosen.publish(103, now=1)
        verdict = chosen.acknowledge("ns2", 101)
        assert "the tap has climbed to 103; it stands" in verdict
        assert "ns2" in chosen.pending

    def test_an_unsent_tap_cannot_be_acknowledged(self):
        with pytest.raises(Invalid):
            notifier().acknowledge("ns2", 101)


class TestTheEconomy:
    def test_the_storm_report_keeps_the_absorbed_visible(self):
        chosen = notifier()
        chosen.publish(101, now=0)
        for serial in (102, 103, 104, 105):
            chosen.publish(serial, now=1)
        report = chosen.storm_report()
        assert "2 tap(s) sent, 8 duplicate(s) absorbed" in report
        assert "names the burst" in report

    def test_the_tap_prices_its_own_purchase(self):
        line = staleness_bought(
            refresh_interval=60, publishes=10, tap_latency=2
        )
        assert "polling alone averages 30" in line
        assert "saving 28 per publish (280 total)" in line

    def test_a_slow_tap_buys_nothing(self):
        with pytest.raises(Invalid):
            staleness_bought(
                refresh_interval=4, publishes=1, tap_latency=5
            )
