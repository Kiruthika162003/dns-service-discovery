from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.zigzag import decode, encode


class TestEncode:
    def test_small_magnitudes_get_small_codes(self):
        assert encode(0) == 0
        assert encode(-1) == 1
        assert encode(1) == 2
        assert encode(-2) == 3
        assert encode(2) == 4

    def test_a_small_negative_is_not_enormous(self):
        # the whole point: -1 encodes to 1, not a huge two's-complement value
        assert encode(-1) == 1


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        for value in (0, 1, -1, 2, -2, 100, -100, 1_000_000, -1_000_000):
            assert decode(encode(value)) == value

    def test_a_negative_code_is_refused(self):
        with pytest.raises(Invalid):
            decode(-1)
