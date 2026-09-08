from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.graycode import from_gray, to_gray


class TestRoundTrip:
    def test_encode_then_decode_is_identity(self):
        for value in range(1000):
            assert from_gray(to_gray(value)) == value


class TestSingleBitChange:
    def test_consecutive_codes_differ_in_one_bit(self):
        for value in range(999):
            difference = to_gray(value) ^ to_gray(value + 1)
            assert bin(difference).count("1") == 1

    def test_zero_encodes_to_zero(self):
        assert to_gray(0) == 0


class TestRefusals:
    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            to_gray(-1)

    def test_a_negative_code_is_refused(self):
        with pytest.raises(Invalid):
            from_gray(-1)
