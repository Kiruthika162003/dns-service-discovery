from __future__ import annotations

import itertools

import pytest

from beacon.errors import Invalid
from beacon.hamming import decode, encode


class TestCleanRoundTrip:
    def test_every_nibble_encodes_and_decodes_cleanly(self):
        for bits in itertools.product([0, 1], repeat=4):
            data = list(bits)
            recovered, syndrome = decode(encode(data))
            assert recovered == data
            assert syndrome == 0


class TestCorrection:
    def test_any_single_bit_error_is_corrected(self):
        for bits in itertools.product([0, 1], repeat=4):
            data = list(bits)
            code = encode(data)
            for position in range(7):
                corrupted = list(code)
                corrupted[position] ^= 1
                recovered, syndrome = decode(corrupted)
                assert recovered == data
                assert syndrome == position + 1


class TestRefusals:
    def test_the_wrong_number_of_data_bits_is_refused(self):
        with pytest.raises(Invalid):
            encode([1, 0, 1])

    def test_a_non_bit_value_is_refused(self):
        with pytest.raises(Invalid):
            encode([0, 1, 2, 0])

    def test_the_wrong_codeword_length_is_refused(self):
        with pytest.raises(Invalid):
            decode([1, 0, 1, 0])
