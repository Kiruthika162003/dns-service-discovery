from __future__ import annotations

import base64

import pytest

from beacon.base32 import decode, encode
from beacon.errors import Invalid


class TestEncode:
    def test_it_matches_the_standard(self):
        for data in (b"", b"f", b"fo", b"foo", b"foobar", b"beacon"):
            assert encode(data) == base64.b32encode(data).decode()

    def test_it_pads_to_a_group_boundary(self):
        # "f" is one byte -> one 5-bit group of data, padded with =
        assert encode(b"f").endswith("=")


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        for data in (b"", b"a", b"abc", b"\x00\xff\x10", b"the beacon"):
            assert decode(encode(data)) == data

    def test_decoding_is_case_insensitive(self):
        upper = encode(b"beacon")
        assert decode(upper.lower()) == b"beacon"


class TestRefusals:
    def test_an_invalid_character_is_refused(self):
        with pytest.raises(Invalid):
            decode("018!")  # 0, 1, 8, ! are not in the alphabet
