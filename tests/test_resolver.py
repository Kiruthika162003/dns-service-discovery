from __future__ import annotations

import pytest

from beacon.errors import Missing, NoData, Refused
from beacon.names import Name
from beacon.records import Record
from beacon.resolver import Resolver
from beacon.zone import Soa, Zone

SOA = Soa(
    serial=1,
    refresh=3600,
    retry=600,
    expire=86400,
    negative_ttl=120,
)


def example_zone() -> Zone:
    zone = Zone(apex=Name.parse("example.com"), soa=SOA)
    zone.add(
        Record(
            name=Name.parse("www.example.com"),
            rtype="A",
            value="192.0.2.10",
            ttl=300,
        )
    )
    zone.add(
        Record(
            name=Name.parse("eu.example.com"),
            rtype="NS",
            value=Name.parse("ns1.eu.example.com"),
            ttl=3600,
        )
    )
    return zone


def eu_zone() -> Zone:
    zone = Zone(apex=Name.parse("eu.example.com"), soa=SOA)
    zone.add(
        Record(
            name=Name.parse("db.eu.example.com"),
            rtype="A",
            value="192.0.2.77",
            ttl=300,
        )
    )
    return zone


def resolver() -> Resolver:
    built = Resolver()
    built.host_zone(example_zone())
    built.host_zone(eu_zone())
    return built


class TestDescent:
    def test_a_direct_answer_takes_one_query(self):
        outcome = resolver().resolve(
            Name.parse("www.example.com"), "A", now=0
        )
        assert outcome.status == "ANSWER"
        assert outcome.upstream_queries == 1

    def test_hosting_the_child_makes_the_descent_free(self):
        outcome = resolver().resolve(
            Name.parse("db.eu.example.com"), "A", now=0
        )
        assert outcome.records[-1].value == "192.0.2.77"
        assert outcome.upstream_queries == 1

    def test_a_dangling_delegation_points_into_the_dark(self):
        chosen = Resolver()
        chosen.host_zone(example_zone())
        with pytest.raises(Refused) as caught:
            chosen.resolve(
                Name.parse("db.eu.example.com"), "A", now=0
            )
        assert "points into the dark" in str(caught.value)

    def test_an_unhosted_name_is_refused_not_invented(self):
        with pytest.raises(Refused) as caught:
            resolver().resolve(Name.parse("other.net"), "A", now=0)
        assert "refuses rather than inventing" in str(
            caught.value
        )


class TestTheCacheEarnsItsKeep:
    def test_the_second_ask_travels_nowhere(self):
        chosen = resolver()
        first = chosen.resolve(
            Name.parse("www.example.com"), "A", now=0
        )
        second = chosen.resolve(
            Name.parse("www.example.com"), "A", now=10
        )
        assert not first.from_cache
        assert second.from_cache
        assert second.upstream_queries == 0
        assert chosen.upstream_total == 1

    def test_the_second_ask_of_a_dead_name_costs_nothing(self):
        chosen = resolver()
        with pytest.raises(Missing):
            chosen.resolve(
                Name.parse("ghost.example.com"), "A", now=0
            )
        with pytest.raises(Missing) as caught:
            chosen.resolve(
                Name.parse("ghost.example.com"), "A", now=10
            )
        assert "nothing travelled" in str(caught.value)
        assert chosen.upstream_total == 1

    def test_nodata_is_remembered_by_type(self):
        chosen = resolver()
        with pytest.raises(NoData):
            chosen.resolve(
                Name.parse("www.example.com"), "TXT", now=0
            )
        with pytest.raises(NoData) as caught:
            chosen.resolve(
                Name.parse("www.example.com"), "TXT", now=5
            )
        assert "nothing travelled" in str(caught.value)
        outcome = chosen.resolve(
            Name.parse("www.example.com"), "A", now=5
        )
        assert outcome.status == "ANSWER"

    def test_the_negative_memory_expires_on_schedule(self):
        chosen = resolver()
        with pytest.raises(Missing):
            chosen.resolve(
                Name.parse("ghost.example.com"), "A", now=0
            )
        with pytest.raises(Missing) as caught:
            chosen.resolve(
                Name.parse("ghost.example.com"), "A", now=120
            )
        assert "nothing travelled" not in str(caught.value)
        assert chosen.upstream_total == 2


class TestTheReport:
    def test_the_descent_report_carries_both_ledgers(self):
        chosen = resolver()
        chosen.resolve(Name.parse("www.example.com"), "A", now=0)
        chosen.resolve(Name.parse("www.example.com"), "A", now=1)
        report = chosen.descent_report()
        assert report.startswith("1 upstream query(ies) total")
        assert "1 hit(s)" in report
