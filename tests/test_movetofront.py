from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.movetofront import decode, encode


class TestRoundTrip:
    def test_encode_then_decode_is_identity(self):
        for data in (b"", b"a", b"banana", bytes(range(256)), b"aaaabbbbcccc"):
            assert decode(encode(data)) == data


class TestSkew:
    def test_a_repeated_byte_becomes_a_run_of_zeros(self):
        positions = encode(b"aaaaaa")
        assert positions[0] != 0  # first occurrence names its slot
        assert positions[1:] == [0, 0, 0, 0, 0]

    def test_the_first_byte_reports_its_own_value(self):
        # with the identity table, byte value equals its starting position
        assert encode(bytes([7]))[0] == 7


class TestRefusals:
    def test_an_out_of_range_position_is_refused(self):
        with pytest.raises(Invalid):
            decode([300])
