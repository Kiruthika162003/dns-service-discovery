from __future__ import annotations

import pytest

from beacon.eliasgamma import decode, encode
from beacon.errors import Invalid


class TestRoundTrip:
    def test_encode_then_decode_is_identity(self):
        values = [1, 2, 3, 4, 10, 255, 1024, 7]
        assert decode(encode(values)) == values

    def test_one_encodes_to_a_single_bit(self):
        assert encode([1]) == "1"

    def test_the_empty_list_encodes_to_the_empty_string(self):
        assert encode([]) == ""
        assert decode("") == []


class TestCompactness:
    def test_small_values_are_shorter_than_large_ones(self):
        assert len(encode([1])) < len(encode([1000]))


class TestRefusals:
    def test_zero_is_refused(self):
        with pytest.raises(Invalid):
            encode([0])

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            encode([-3])

    def test_a_truncated_value_field_is_refused(self):
        # "001" promises a three-bit value but supplies only one bit
        with pytest.raises(Invalid):
            decode("001")
