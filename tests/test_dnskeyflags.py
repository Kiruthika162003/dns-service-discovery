from __future__ import annotations

import pytest

from beacon.dnskeyflags import (
    REVOKE,
    SEP,
    ZONE,
    is_revoked,
    is_sep,
    is_zone_key,
    may_sign,
)
from beacon.errors import Invalid


class TestClassification:
    def test_a_zone_key_is_recognized(self):
        assert is_zone_key(ZONE)

    def test_a_ksk_sets_zone_and_sep(self):
        flags = ZONE | SEP
        assert is_zone_key(flags)
        assert is_sep(flags)

    def test_a_revoked_key_is_recognized(self):
        assert is_revoked(ZONE | REVOKE)


class TestMaySign:
    def test_a_live_zone_key_may_sign(self):
        assert may_sign(ZONE)

    def test_a_revoked_zone_key_may_not(self):
        assert not may_sign(ZONE | REVOKE)

    def test_a_non_zone_key_is_refused(self):
        with pytest.raises(Invalid) as caught:
            may_sign(SEP)  # SEP set but ZONE not
        assert "must reject its signatures" in str(caught.value)
