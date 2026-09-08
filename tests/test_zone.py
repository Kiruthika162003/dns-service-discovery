from __future__ import annotations

import pytest

from beacon.errors import Invalid, Loop, Missing, NoData
from beacon.names import Name
from beacon.records import Record
from beacon.zone import Soa, Zone

APEX = Name.parse("example.com")
SOA = Soa(
    serial=2026090801,
    refresh=3600,
    retry=600,
    expire=86400,
    negative_ttl=300,
)


def zone() -> Zone:
    built = Zone(apex=APEX, soa=SOA)
    built.add(
        Record(
            name=Name.parse("www.example.com"),
            rtype="A",
            value="192.0.2.10",
            ttl=300,
        )
    )
    built.add(
        Record(
            name=Name.parse("blog.example.com"),
            rtype="CNAME",
            value=Name.parse("www.example.com"),
            ttl=300,
        )
    )
    built.add(
        Record(
            name=Name.parse("*.dev.example.com"),
            rtype="A",
            value="192.0.2.99",
            ttl=60,
        )
    )
    built.add(
        Record(
            name=Name.parse("eu.example.com"),
            rtype="NS",
            value=Name.parse("ns1.eu-host.net"),
            ttl=3600,
        )
    )
    return built


class TestTheTwoNos:
    def test_a_missing_name_is_nxdomain(self):
        with pytest.raises(Missing) as caught:
            zone().lookup(Name.parse("ghost.example.com"), "A")
        assert "does not exist" in str(caught.value)
        assert "negative ttl 300" in str(caught.value)

    def test_a_present_name_without_the_type_is_nodata(self):
        with pytest.raises(NoData) as caught:
            zone().lookup(Name.parse("www.example.com"), "TXT")
        assert "not-that is a different answer from no" in str(
            caught.value
        )


class TestAnswers:
    def test_the_direct_answer_comes_back(self):
        status, rows = zone().lookup(
            Name.parse("WWW.example.com"), "A"
        )
        assert status == "ANSWER"
        assert rows[0].value == "192.0.2.10"

    def test_the_cname_chain_rides_along(self):
        status, rows = zone().lookup(
            Name.parse("blog.example.com"), "A"
        )
        assert status == "ANSWER"
        assert rows[0].rtype == "CNAME"
        assert rows[1].value == "192.0.2.10"

    def test_the_wildcard_synthesizes_under_its_stem(self):
        status, rows = zone().lookup(
            Name.parse("anything.dev.example.com"), "A"
        )
        assert status == "ANSWER"
        assert rows[0].name.canonical() == (
            "anything.dev.example.com."
        )
        assert rows[0].value == "192.0.2.99"

    def test_an_explicit_name_blocks_the_wildcard(self):
        built = zone()
        built.add(
            Record(
                name=Name.parse("real.dev.example.com"),
                rtype="TXT",
                value=b"pinned",
                ttl=60,
            )
        )
        with pytest.raises(NoData):
            built.lookup(Name.parse("real.dev.example.com"), "A")


class TestDelegation:
    def test_below_the_cut_the_zone_refers(self):
        status, rows = zone().lookup(
            Name.parse("db.eu.example.com"), "A"
        )
        assert status == "REFERRAL"
        assert rows[0].rtype == "NS"

    def test_outside_the_subtree_is_someone_elses_question(self):
        with pytest.raises(Invalid) as caught:
            zone().lookup(Name.parse("other.net"), "A")
        assert "ask a server that answers for it" in str(
            caught.value
        )


class TestCnameDiscipline:
    def test_an_alias_may_hold_nothing_else(self):
        built = zone()
        with pytest.raises(Invalid) as caught:
            built.add(
                Record(
                    name=Name.parse("blog.example.com"),
                    rtype="A",
                    value="192.0.2.44",
                    ttl=60,
                )
            )
        assert "two answers to one question" in str(caught.value)

    def test_the_apex_cannot_be_an_alias(self):
        with pytest.raises(Invalid) as caught:
            zone().add(
                Record(
                    name=APEX,
                    rtype="CNAME",
                    value=Name.parse("elsewhere.net"),
                    ttl=60,
                )
            )
        assert "SOA and NS must live somewhere" in str(
            caught.value
        )

    def test_circular_aliases_are_caught_by_the_guard(self):
        built = Zone(apex=APEX, soa=SOA)
        built.add(
            Record(
                name=Name.parse("a.example.com"),
                rtype="CNAME",
                value=Name.parse("b.example.com"),
                ttl=60,
            )
        )
        built.add(
            Record(
                name=Name.parse("b.example.com"),
                rtype="CNAME",
                value=Name.parse("a.example.com"),
                ttl=60,
            )
        )
        with pytest.raises(Loop) as caught:
            built.lookup(Name.parse("a.example.com"), "A")
        assert "aliases pointing in circles" in str(caught.value)
