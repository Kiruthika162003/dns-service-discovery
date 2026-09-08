from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.hostsfile import HostsFile


def hosts() -> HostsFile:
    built = HostsFile()
    built.add("payments.example.com.", "10.9.9.9", now=0)
    built.add("db.example.com.", "10.0.0.5", now=500)
    return built


class TestTheOverride:
    def test_the_hit_is_stamped_never_silent(self):
        verdict = hosts().lookup(
            "payments.example.com.", now=100
        )
        assert "[OVERRIDE from hosts, 100 tick(s) old]" in (
            verdict
        )
        assert "before anyone is asked" in verdict

    def test_a_miss_falls_through_to_dns(self):
        assert hosts().lookup("www.example.com.", now=0) is None


class TestTheAgeAudit:
    def test_stale_suspects_come_oldest_first(self):
        report = hosts().age_audit(now=1000, stale_after=400)
        assert "2 stale suspect(s), oldest first" in report
        lines = report.splitlines()
        assert "payments.example.com." in lines[1]
        assert "1000 tick(s) old" in lines[1]

    def test_a_young_file_remembers_its_reasons(self):
        report = hosts().age_audit(now=100, stale_after=400)
        assert "young enough to remember its reasons" in report

    def test_staleness_needs_a_horizon(self):
        with pytest.raises(Invalid):
            hosts().age_audit(now=100, stale_after=0)


class TestTheLint:
    def test_the_double_mapping_names_the_silent_winner(self):
        built = hosts()
        built.add("db.example.com.", "10.0.0.6", now=600)
        wounds = built.lint()
        assert len(wounds) == 1
        assert "10.0.0.5 wins silently over 10.0.0.6" in (
            wounds[0]
        )

    def test_the_loopback_wound_is_the_authors_laptop(self):
        built = hosts()
        built.add("api.example.com.", "127.0.0.1", now=0)
        wounds = built.lint()
        assert "works only on its author's laptop" in wounds[0]

    def test_localhost_to_loopback_is_not_a_wound(self):
        built = HostsFile()
        built.add("localhost", "127.0.0.1", now=0)
        assert built.lint() == []
