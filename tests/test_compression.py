from __future__ import annotations

import pytest

from beacon.compression import decompress
from beacon.errors import Invalid, Loop


class TestDecompression:
    def test_a_plain_name_reads_its_labels(self):
        # 0: www -> 4: example -> 12: "" (root)
        entries = {
            0: ("label", "www", 4),
            4: ("label", "example", 12),
            12: ("label", "", 0),
        }
        assert decompress(entries, 0) == ["www", "example"]

    def test_a_backward_pointer_reuses_an_earlier_suffix(self):
        # mail(20) -> pointer to example(4); example(4) -> root(12)
        entries = {
            4: ("label", "example", 12),
            12: ("label", "", 0),
            20: ("label", "mail", 24),
            24: ("pointer", 4),
        }
        assert decompress(entries, 20) == ["mail", "example"]


class TestTheAttack:
    def test_a_self_pointer_is_refused(self):
        entries = {8: ("pointer", 8)}
        with pytest.raises(Invalid) as caught:
            decompress(entries, 8)
        assert "decompression-loop attack" in str(caught.value)

    def test_a_forward_pointer_is_refused(self):
        entries = {4: ("pointer", 40), 40: ("label", "", 0)}
        with pytest.raises(Invalid):
            decompress(entries, 4)

    def test_a_cycle_of_backward_pointers_is_caught(self):
        # 20 -> 10 -> 20 : each step backward at the hop, but a cycle
        entries = {20: ("pointer", 10), 10: ("label", "a", 20)}
        with pytest.raises(Loop):
            decompress(entries, 20)

    def test_a_dangling_pointer_is_refused(self):
        entries = {4: ("pointer", 2)}
        with pytest.raises(Invalid) as caught:
            decompress(entries, 4)
        assert "dangling pointer" in str(caught.value)
