from __future__ import annotations

from collections import Counter

import pytest

from beacon.errors import Invalid
from beacon.huffman import build_codes, decode, encode


class TestCodes:
    def test_frequent_symbols_get_shorter_codes(self):
        codes = build_codes({"a": 100, "b": 5, "c": 5})
        assert len(codes["a"]) <= len(codes["b"])

    def test_the_code_is_prefix_free(self):
        codes = build_codes(Counter("abracadabra"))
        values = list(codes.values())
        assert all(
            not a.startswith(b)
            for a in values
            for b in values
            if a != b
        )

    def test_a_single_symbol_gets_a_one_bit_code(self):
        assert build_codes({"a": 10}) == {"a": "0"}

    def test_no_symbols_is_refused(self):
        with pytest.raises(Invalid):
            build_codes({})


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        message = "abracadabra"
        codes = build_codes(Counter(message))
        assert decode(encode(message, codes), codes) == message

    def test_it_compresses_a_skewed_message(self):
        message = "aaaaaaaaab"
        codes = build_codes(Counter(message))
        assert len(encode(message, codes)) < len(message) * 8

    def test_an_unknown_symbol_is_refused(self):
        codes = build_codes({"a": 1, "b": 1})
        with pytest.raises(Invalid):
            encode("c", codes)
