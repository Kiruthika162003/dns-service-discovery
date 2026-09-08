from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.varint import decode, encode


class TestEncode:
    def test_a_small_number_is_one_byte(self):
        assert encode(1) == b"\x01"
        assert encode(127) == b"\x7f"

    def test_128_needs_two_bytes(self):
        assert encode(128) == b"\x80\x01"

    def test_a_negative_number_is_refused(self):
        with pytest.raises(Invalid):
            encode(-1)


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        for value in (0, 1, 127, 128, 300, 16384, 1_000_000):
            data = encode(value)
            decoded, consumed = decode(data)
            assert decoded == value
            assert consumed == len(data)

    def test_decode_reports_bytes_consumed_from_a_stream(self):
        stream = encode(300) + encode(5)
        value, consumed = decode(stream)
        assert value == 300
        rest_value, _ = decode(stream[consumed:])
        assert rest_value == 5


class TestTruncation:
    def test_a_dangling_continuation_is_refused(self):
        with pytest.raises(Invalid) as caught:
            decode(b"\x80\x80")  # every byte says "more follows"
        assert "truncated" in str(caught.value)
