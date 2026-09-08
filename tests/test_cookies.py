from __future__ import annotations

import pytest

from beacon.cookies import CookieServer, _server_cookie
from beacon.errors import Invalid


def server() -> CookieServer:
    return CookieServer(secret="zone-secret-2026")


class TestBootstrap:
    def test_first_contact_is_cookie_optional(self):
        chosen = server()
        verdict = chosen.respond("client-nonce-1", None)
        assert "first contact: issuing server cookie" in verdict
        assert "new clients are not locked out" in verdict
        assert chosen.bootstraps == 1

    def test_a_missing_client_cookie_cannot_be_protected(self):
        with pytest.raises(Invalid):
            server().respond("", None)

    def test_dropping_a_known_client_is_a_downgrade(self):
        chosen = server()
        chosen.respond("client-nonce-1", None)
        with pytest.raises(Invalid) as caught:
            chosen.respond("client-nonce-1", None)
        assert "a downgrade an on-path attacker would love" in (
            str(caught.value)
        )


class TestVerification:
    def test_the_right_cookie_is_served(self):
        chosen = server()
        chosen.respond("client-nonce-1", None)
        cookie = _server_cookie(
            "client-nonce-1", "zone-secret-2026"
        )
        verdict = chosen.respond("client-nonce-1", cookie)
        assert "cookie verified, answer served" in verdict

    def test_the_forgery_is_dropped_before_the_records(self):
        chosen = server()
        chosen.respond("client-nonce-1", None)
        with pytest.raises(Invalid) as caught:
            chosen.respond("client-nonce-1", "forged-cookie")
        assert "never saw the cookie to echo it" in str(
            caught.value
        )
        assert chosen.forgeries_dropped == 1


class TestHonesty:
    def test_the_on_path_limit_is_stated_plainly(self):
        note = server().on_path_note()
        assert "instead of overselling" in note

    def test_the_ledger_counts_the_defense(self):
        chosen = server()
        chosen.respond("client-nonce-1", None)
        with pytest.raises(Invalid):
            chosen.respond("client-nonce-1", "forged")
        ledger = chosen.ledger()
        assert "1 bootstrap(s), 1 known client(s)" in ledger
        assert "1 off-path forgery(ies) dropped" in ledger
