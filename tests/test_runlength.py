from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.runlength import decode, encode


class TestEncode:
    def test_it_collapses_runs(self):
        assert encode(["a", "a", "a", "b", "b", "c"]) == [
            ("a", 3),
            ("b", 2),
            ("c", 1),
        ]

    def test_an_empty_sequence_encodes_to_nothing(self):
        assert encode([]) == []

    def test_varied_data_gets_no_shorter(self):
        # the weakness: no runs means one pair per element
        assert encode(["a", "b", "c"]) == [("a", 1), ("b", 1), ("c", 1)]


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        data = ["x", "x", "y", "z", "z", "z"]
        assert decode(encode(data)) == data

    def test_a_nonpositive_count_is_refused(self):
        with pytest.raises(Invalid):
            decode([("a", 0)])
