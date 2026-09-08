from __future__ import annotations

import pytest

from beacon.contentchunking import boundaries
from beacon.errors import Invalid

DATA = bytes((i * 73 + 11) % 256 for i in range(400))


class TestBoundaries:
    def test_it_finds_content_boundaries(self):
        cuts = boundaries(DATA, window=8, mask=0x0F)
        assert len(cuts) > 0

    def test_a_larger_mask_yields_fewer_boundaries(self):
        fine = boundaries(DATA, window=8, mask=0x07)
        coarse = boundaries(DATA, window=8, mask=0x3F)
        assert len(coarse) < len(fine)


class TestShiftResistance:
    def test_prepending_shifts_boundaries_by_the_prefix_only(self):
        prefix = bytes([5, 5, 5, 5, 5])
        shifted = boundaries(prefix + DATA, window=8, mask=0x0F)
        original = boundaries(DATA, window=8, mask=0x0F)
        shifted_set = set(shifted)
        # every original boundary reappears shifted by the prefix length
        assert all(cut + len(prefix) in shifted_set for cut in original)


class TestRefusals:
    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            boundaries(DATA, window=0, mask=0x0F)

    def test_a_zero_mask_is_refused(self):
        with pytest.raises(Invalid):
            boundaries(DATA, window=8, mask=0)
