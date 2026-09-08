from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.trustanchor import TrustAnchors


class TestHoldDown:
    def test_a_freshly_seen_key_is_pending_not_trusted(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("ksk-2", now=0)
        assert anchors.is_pending("ksk-2", now=10)
        assert not anchors.is_trusted("ksk-2", now=10)

    def test_a_key_seen_past_the_hold_down_is_trusted(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("ksk-2", now=0)
        assert anchors.is_trusted("ksk-2", now=30)

    def test_a_flickering_key_never_crosses_the_threshold(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("attacker", now=0)
        assert not anchors.is_trusted("attacker", now=29)

    def test_the_first_sighting_anchors_the_clock(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("ksk-2", now=100)
        anchors.observe("ksk-2", now=120)
        assert not anchors.is_trusted("ksk-2", now=125)
        assert anchors.is_trusted("ksk-2", now=130)


class TestRevocation:
    def test_a_revoked_key_is_no_longer_trusted(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("ksk-1", now=0)
        assert anchors.is_trusted("ksk-1", now=30)
        anchors.observe("ksk-1", now=40, revoke_bit=True)
        assert not anchors.is_trusted("ksk-1", now=50)

    def test_revoking_an_unseen_key_is_refused_as_noise(self):
        anchors = TrustAnchors()
        with pytest.raises(Invalid) as caught:
            anchors.observe("ghost", now=0, revoke_bit=True)
        assert "unattributable noise" in str(caught.value)


class TestActiveSet:
    def test_active_holds_only_the_matured_unrevoked_keys(self):
        anchors = TrustAnchors(add_hold_down=30)
        anchors.observe("old", now=0)
        anchors.observe("new", now=20)
        assert anchors.active(now=35) == {"old"}
