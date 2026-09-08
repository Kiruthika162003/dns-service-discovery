from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.keytag import key_tag, tags_collide


class TestComputation:
    def test_the_tag_is_a_16_bit_value(self):
        tag = key_tag(b"\x08\x01\x03\x04\xde\xad\xbe\xef")
        assert 0 <= tag <= 0xFFFF

    def test_the_tag_is_deterministic(self):
        rdata = b"\x01\x02\x03\x04"
        assert key_tag(rdata) == key_tag(rdata)

    def test_empty_rdata_is_refused(self):
        with pytest.raises(Invalid):
            key_tag(b"")


class TestNotAFingerprint:
    def test_two_different_keys_can_share_a_tag(self):
        # both sum to the same 16-bit words, so the tag collides
        a = b"\x01\x00\x00\x00"
        b = b"\x00\x00\x01\x00"
        assert key_tag(a) == key_tag(b)
        assert tags_collide(a, b)

    def test_identical_rdata_is_not_a_collision(self):
        assert not tags_collide(b"\x01\x02", b"\x01\x02")
