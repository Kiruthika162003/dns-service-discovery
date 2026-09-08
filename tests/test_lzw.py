from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lzw import compress, decompress


class TestRoundTrip:
    def test_encode_decode_is_identity(self):
        for data in (
            b"",
            b"a",
            b"TOBEORNOTTOBEORTOBEORNOT",
            bytes(range(256)),
        ):
            assert decompress(compress(data)) == data

    def test_the_same_step_case_roundtrips(self):
        # ababab and aaaa exercise a code used the step it is defined
        assert decompress(compress(b"ababababab")) == b"ababababab"
        assert decompress(compress(b"aaaaaaaa")) == b"aaaaaaaa"


class TestCompression:
    def test_repetitive_data_shrinks(self):
        data = b"TOBEORNOTTOBEORTOBEORNOT"
        assert len(compress(data)) < len(data)

    def test_a_single_symbol_run_shrinks(self):
        assert len(compress(b"aaaaaaaaaaaa")) < 12


class TestRefusals:
    def test_a_corrupt_code_is_refused(self):
        with pytest.raises(Invalid):
            decompress([256])  # 256 is neither known nor next-to-define at start
