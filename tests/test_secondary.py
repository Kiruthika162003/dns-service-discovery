from __future__ import annotations

import pytest

from beacon.errors import Expired, Invalid
from beacon.names import Name
from beacon.records import Record
from beacon.secondary import Secondary
from beacon.transfers import TransferPrimary


def a_record(host: str) -> Record:
    return Record(
        name=Name.parse(f"{host}.example.com"),
        rtype="A",
        value="192.0.2.1",
        ttl=300,
    )


def pair() -> tuple[TransferPrimary, Secondary]:
    primary = TransferPrimary(serial=100)
    primary.publish(101, [a_record("www")], [])
    secondary = Secondary(
        name="ns2", refresh=60, retry=15, expire=600
    )
    secondary.bootstrap(primary, now=0)
    return primary, secondary


class TestTheLifecycle:
    def test_a_broken_soa_chases_its_tail(self):
        with pytest.raises(Invalid):
            Secondary(name="x", refresh=10, retry=20, expire=600)

    def test_bootstrap_takes_the_full_copy(self):
        _, secondary = pair()
        assert secondary.serial == 101
        assert secondary.holds_copy

    def test_refresh_advances_by_deltas(self):
        primary, secondary = pair()
        primary.publish(102, [a_record("api")], [])
        verdict = secondary.attempt_refresh(
            primary, now=60, reachable=True
        )
        assert "advanced to serial 102 via 1 delta(s)" in verdict

    def test_the_quiet_zone_is_a_cheap_refresh(self):
        primary, secondary = pair()
        verdict = secondary.attempt_refresh(
            primary, now=60, reachable=True
        )
        assert "current at serial 101" in verdict


class TestDueness:
    def test_success_schedules_by_refresh(self):
        primary, secondary = pair()
        secondary.attempt_refresh(primary, now=60, reachable=True)
        assert not secondary.due(now=100)
        assert secondary.due(now=120)

    def test_failure_schedules_by_retry(self):
        primary, secondary = pair()
        secondary.attempt_refresh(
            primary, now=60, reachable=False
        )
        assert not secondary.due(now=70)
        assert secondary.due(now=75)


class TestServing:
    def test_fresh_serves_fresh(self):
        _, secondary = pair()
        assert "serving fresh" in secondary.serve(now=30)

    def test_stale_beats_silent_during_the_outage(self):
        primary, secondary = pair()
        secondary.attempt_refresh(
            primary, now=60, reachable=False
        )
        verdict = secondary.serve(now=90)
        assert "stale beats silent" in verdict
        assert secondary.stale_served == 1

    def test_past_expire_the_copy_is_fiction(self):
        _, secondary = pair()
        with pytest.raises(Expired) as caught:
            secondary.serve(now=600)
        assert "fiction with a domain name" in str(caught.value)

    def test_expire_counts_from_success_not_attempt(self):
        primary, secondary = pair()
        for tick in range(15, 600, 15):
            secondary.attempt_refresh(
                primary, now=tick, reachable=False
            )
        assert not secondary.answerable(now=600)


class TestFreshness:
    def test_the_census_names_the_gap(self):
        primary, secondary = pair()
        primary.publish(102, [a_record("api")], [])
        report = secondary.freshness(primary.serial)
        assert report == "ns2: behind (has 101, primary at 102)"
