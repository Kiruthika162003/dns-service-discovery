from __future__ import annotations

import zlib

from beacon.crc import crc32


class TestCrc32:
    def test_it_matches_the_standard(self):
        for data in (b"", b"beacon", b"123456789", b"The quick brown fox"):
            assert crc32(data) == zlib.crc32(data)

    def test_the_check_value(self):
        # the well-known CRC-32 check value for "123456789"
        assert crc32(b"123456789") == 0xCBF43926

    def test_it_is_deterministic(self):
        assert crc32(b"payload") == crc32(b"payload")


class TestDetection:
    def test_a_single_bit_flip_changes_the_crc(self):
        assert crc32(b"beacon") != crc32(b"beacom")

    def test_a_transposition_changes_the_crc(self):
        assert crc32(b"ab") != crc32(b"ba")
