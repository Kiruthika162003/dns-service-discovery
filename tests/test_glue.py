from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.glue import GlueAuditor
from beacon.names import Name


def auditor() -> GlueAuditor:
    return GlueAuditor(apex=Name.parse("example.com"))


class TestTheChickenAndEgg:
    def test_in_bailiwick_without_glue_is_a_deadlock(self):
        chosen = auditor()
        chosen.delegate(
            "eu.example.com", ["ns1.eu.example.com"]
        )
        report = chosen.audit()
        assert "1 deadlock(s)" in report
        assert "deadlocks politely forever" in report

    def test_glue_resolves_the_deadlock(self):
        chosen = auditor()
        chosen.delegate(
            "eu.example.com",
            ["ns1.eu.example.com"],
            glue={"ns1.eu.example.com.": "192.0.2.53"},
        )
        report = chosen.audit()
        assert report.startswith("1 delegation edge(s) healthy")

    def test_outside_nameservers_need_no_courtesy(self):
        chosen = auditor()
        chosen.delegate(
            "eu.example.com", ["ns1.host-corp.net"]
        )
        assert chosen.audit().startswith(
            "1 delegation edge(s) healthy"
        )

    def test_unnecessary_glue_is_stale_courtesy(self):
        chosen = auditor()
        chosen.delegate(
            "eu.example.com",
            ["ns1.host-corp.net"],
            glue={"ns1.host-corp.net.": "203.0.113.53"},
        )
        report = chosen.audit()
        assert "1 stale courtesy record(s)" in report
        assert "old house" in report

    def test_one_delegates_only_what_one_holds(self):
        with pytest.raises(Invalid) as caught:
            auditor().delegate("other.net", ["ns1.other.net"])
        assert "only what one holds" in str(caught.value)


class TestMixedDelegations:
    def test_each_edge_is_judged_alone(self):
        chosen = auditor()
        chosen.delegate(
            "eu.example.com",
            [
                "ns1.eu.example.com",
                "ns2.host-corp.net",
            ],
            glue={"ns1.eu.example.com.": "192.0.2.53"},
        )
        report = chosen.audit()
        assert report.startswith(
            "2 delegation edge(s) healthy, 0 deadlock(s)"
        )
