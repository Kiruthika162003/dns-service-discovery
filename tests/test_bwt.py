from __future__ import annotations

from itertools import groupby

import pytest

from beacon.bwt import invert, transform
from beacon.errors import Invalid


class TestRoundTrip:
    def test_transform_then_invert_is_identity(self):
        for word in (b"banana", b"mississippi", b"abracadabra", b"a", b""):
            last_column, index = transform(word)
            assert invert(last_column, index) == word


class TestClustering:
    def test_repeated_context_produces_runs(self):
        # the transform of a repetitive block has runs a raw block lacks
        last_column, _ = transform(b"abababababab")
        longest_run = max(
            len(list(group))
            for group in _runs(last_column)
        )
        assert longest_run >= 4


class TestRefusals:
    def test_a_block_containing_the_sentinel_is_refused(self):
        with pytest.raises(Invalid):
            transform(b"a\x00b")

    def test_an_out_of_range_index_is_refused(self):
        last_column, _ = transform(b"hello")
        with pytest.raises(Invalid):
            invert(last_column, 999)

    def test_an_empty_last_column_is_refused(self):
        with pytest.raises(Invalid):
            invert(b"", 0)


def _runs(data: bytes):
    return [list(group) for _, group in groupby(data)]
