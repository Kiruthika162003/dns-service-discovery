from __future__ import annotations

import pytest

from beacon.acl import ZoneAcl
from beacon.errors import Invalid, Refused


def acl() -> ZoneAcl:
    built = ZoneAcl(zone="corp.example.", query_open=False)
    built.query_allow.add("10.0.0.0/8")
    built.grant_transfer("ns2.corp.example.")
    return built


class TestQueries:
    def test_the_open_zone_answers_anyone(self):
        open_acl = ZoneAcl(zone="public.example.")
        assert "may query" in open_acl.check_query("anywhere")

    def test_the_closed_zone_refuses_deliberately(self):
        with pytest.raises(Refused) as caught:
            acl().check_query("203.0.113.5")
        assert "a wall it cannot see" in str(caught.value)

    def test_the_flood_case_drops_silently(self):
        chosen = acl()
        verdict = chosen.check_query(
            "203.0.113.5", flooding=True
        )
        assert "amplification currency" in verdict
        assert chosen.silent_drops == 1

    def test_the_allowed_network_passes(self):
        assert "may query" in acl().check_query("10.0.0.0/8")


class TestTransfers:
    def test_the_database_does_not_walk_without_a_key(self):
        with pytest.raises(Refused) as caught:
            acl().check_transfer("203.0.113.5")
        assert "walking out the door" in str(caught.value)

    def test_the_keyholder_transfers(self):
        assert "may transfer" in acl().check_transfer(
            "ns2.corp.example."
        )

    def test_keys_grant_once_and_revoke_once(self):
        chosen = acl()
        with pytest.raises(Invalid):
            chosen.grant_transfer("ns2.corp.example.")
        chosen.revoke_transfer("ns2.corp.example.")
        with pytest.raises(Invalid):
            chosen.revoke_transfer("ns2.corp.example.")


class TestTheKeyAudit:
    def test_the_departed_employees_pocket_is_named(self):
        chosen = acl()
        chosen.grant_transfer("old-ns.corp.example.")
        findings = chosen.key_audit(
            active_secondaries={"ns2.corp.example."}
        )
        assert len(findings) == 1
        assert "departed employee's pocket" in findings[0]

    def test_active_keys_pass_the_audit(self):
        assert acl().key_audit(
            active_secondaries={"ns2.corp.example."}
        ) == []
