from __future__ import annotations

import pytest

from beacon.dohrouting import (
    PROFILES,
    TransportProfile,
    comparison_table,
    recommend,
)
from beacon.errors import Invalid


class TestProfiles:
    def test_plaintext_is_readable_and_blockable(self):
        profile = PROFILES["plaintext"]
        assert profile.network_can_read
        assert profile.network_can_block_by_port

    def test_doh_is_opaque_and_hidden_at_a_cost(self):
        profile = PROFILES["doh"]
        assert not profile.network_can_read
        assert not profile.network_can_block_by_port
        assert profile.handshake_cost == 5

    def test_an_unknown_transport_is_refused(self):
        with pytest.raises(Invalid):
            TransportProfile("carrier-pigeon", False, False, 1)


class TestRecommendation:
    def test_the_eavesdropper_gets_dot_not_doh(self):
        rec = recommend("passive-eavesdropper")
        assert rec.startswith("dot:")
        assert "cargo cult with encryption" in rec

    def test_the_firewall_gets_doh(self):
        rec = recommend("port-blocking-firewall")
        assert rec.startswith("doh:")
        assert "survives a firewall that blocks 853" in rec

    def test_no_threat_gets_plaintext(self):
        rec = recommend("none")
        assert rec.startswith("plaintext:")
        assert "defending against nobody" in rec

    def test_an_unnamed_threat_is_refused(self):
        with pytest.raises(Invalid) as caught:
            recommend("vibes")
        assert "cargo cult with encryption" in str(caught.value)


class TestTheTable:
    def test_the_table_crowns_nobody(self):
        table = comparison_table()
        assert "plaintext: readable, blockable, handshake 0" in (
            table
        )
        assert "doh: opaque, hidden, handshake 5" in table
        assert "not a default" in table
