from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.pinning import PinSet


def pinset() -> PinSet:
    built = PinSet(ttl=30)
    built.publish_new("old-cert-fingerprint", now=0)
    return built


class TestPublishAndValidate:
    def test_a_matching_certificate_validates(self):
        verdict = pinset().validate("old-cert-fingerprint")
        assert "matches an active pin" in verdict

    def test_a_valid_cert_off_the_pin_is_rejected_with_the_reason(self):
        with pytest.raises(Invalid) as caught:
            pinset().validate("brand-new-cert")
        assert "not updated before rotation" in str(caught.value)

    def test_republishing_an_active_pin_is_refused(self):
        with pytest.raises(Invalid):
            pinset().publish_new("old-cert-fingerprint", now=5)


class TestTheOverlapDiscipline:
    def test_retiring_before_the_ttl_strands_caches(self):
        chosen = pinset()
        chosen.publish_new("new-cert-fingerprint", now=10)
        with pytest.raises(Invalid) as caught:
            chosen.retire("old-cert-fingerprint", now=20)
        assert "rejecting the live certificate" in str(
            caught.value
        )

    def test_the_full_overlap_permits_retirement(self):
        chosen = pinset()
        chosen.publish_new("new-cert-fingerprint", now=10)
        verdict = chosen.retire("old-cert-fingerprint", now=40)
        assert "overlap held" in verdict
        assert "old-cert-fingerprint" not in chosen.active_pins

    def test_retiring_the_last_pin_is_refused(self):
        with pytest.raises(Invalid) as caught:
            pinset().retire("old-cert-fingerprint", now=100)
        assert "publish the new one first" in str(caught.value)

    def test_a_zero_ttl_pinset_is_refused(self):
        with pytest.raises(Invalid):
            PinSet(ttl=0)


class TestTheHorizon:
    def test_the_near_expiry_names_the_dated_outage(self):
        report = pinset().expiry_horizon(
            cert_expires_at=20, now=0
        )
        assert "inside the pin ttl of 30" in report
        assert "a date already on it" in report

    def test_a_distant_expiry_has_room(self):
        report = pinset().expiry_horizon(
            cert_expires_at=500, now=0
        )
        assert "room to rotate the pin safely" in report
