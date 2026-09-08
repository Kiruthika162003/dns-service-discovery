from __future__ import annotations

from beacon.inetchecksum import checksum, verify

HEADER = bytes(
    [
        0x45, 0x00, 0x00, 0x3C, 0x1C, 0x46, 0x40, 0x00,
        0x40, 0x06, 0x00, 0x00, 0xAC, 0x10, 0x0A, 0x63,
        0xAC, 0x10, 0x0A, 0x0C,
    ]
)


class TestChecksum:
    def test_it_is_deterministic(self):
        assert checksum(HEADER) == checksum(HEADER)

    def test_it_verifies_intact_data(self):
        assert verify(HEADER, checksum(HEADER))

    def test_an_odd_length_is_padded(self):
        # a single byte still produces a checksum
        assert 0 <= checksum(b"\x12") <= 0xFFFF


class TestDetection:
    def test_a_bit_flip_fails_verification(self):
        c = checksum(HEADER)
        corrupted = bytearray(HEADER)
        corrupted[0] ^= 0x01
        assert not verify(bytes(corrupted), c)


class TestBlindness:
    def test_swapping_two_words_is_not_detected(self):
        # the honest weakness: a sum is blind to reordering
        assert checksum(b"\x00\x01\x00\x02") == checksum(b"\x00\x02\x00\x01")
