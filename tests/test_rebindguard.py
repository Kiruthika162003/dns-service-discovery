from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.rebindguard import RebindGuard, lands_inside


class TestTheBoundary:
    def test_the_private_families_land_inside(self):
        for address in (
            "10.0.0.5",
            "192.168.1.9",
            "127.0.0.1",
            "169.254.9.9",
            "172.20.1.1",
        ):
            assert lands_inside(address)

    def test_public_space_stays_outside(self):
        assert not lands_inside("203.0.113.10")
        assert not lands_inside("172.15.0.1")


class TestTheGuard:
    def test_outside_answers_pass_untouched(self):
        verdict = RebindGuard().admit(
            "cdn.example.net.", "203.0.113.10", now=0
        )
        assert "outside stays outside" in verdict

    def test_the_flip_to_inside_is_refused_and_logged(self):
        guard = RebindGuard()
        with pytest.raises(Refused) as caught:
            guard.admit("evil.example.net.", "10.0.0.5", now=7)
        assert "no honest reason" in str(caught.value)
        assert len(guard.refusals) == 1

    def test_the_declared_carveout_is_exact_match(self):
        guard = RebindGuard()
        guard.allow("vpn.corp.example.")
        verdict = guard.admit(
            "vpn.corp.example.", "10.8.0.1", now=0
        )
        assert "declared carve-out" in verdict
        with pytest.raises(Refused):
            guard.admit("evil.corp.example.", "10.8.0.2", now=1)

    def test_wildcard_exceptions_are_a_resignation(self):
        with pytest.raises(Invalid) as caught:
            RebindGuard().allow("*.corp.example.")
        assert "resigning with a notice period" in str(
            caught.value
        )


class TestTheAudit:
    def test_the_page_shows_carveouts_and_recent_refusals(self):
        guard = RebindGuard()
        guard.allow("vpn.corp.example.")
        with pytest.raises(Refused):
            guard.admit("evil.net.", "10.1.1.1", now=3)
        page = guard.audit_page()
        assert "1 carve-out(s), 1 rebind refusal(s)" in page
        assert "allowed: vpn.corp.example." in page
        assert "[3] evil.net. -> 10.1.1.1 REFUSED" in page
