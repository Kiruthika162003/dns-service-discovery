from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.memtable import MemTable


class TestBuffering:
    def test_writes_buffer_until_the_threshold(self):
        table = MemTable(threshold=3)
        assert table.put("a", "1") == "buffered"
        assert table.put("b", "2") == "buffered"
        assert table.put("c", "3") == "flush-due"

    def test_a_zero_threshold_is_refused(self):
        with pytest.raises(Invalid):
            MemTable(threshold=0)


class TestFlush:
    def test_the_flush_is_sorted(self):
        table = MemTable(threshold=3)
        table.put("c", "3")
        table.put("a", "1")
        table.put("b", "2")
        assert table.flush() == [("a", "1"), ("b", "2"), ("c", "3")]

    def test_flush_clears_the_table(self):
        table = MemTable(threshold=2)
        table.put("a", "1")
        table.flush()
        assert table.size() == 0

    def test_flushing_empty_is_refused(self):
        with pytest.raises(Invalid):
            MemTable(threshold=2).flush()

    def test_a_later_put_overwrites_within_the_buffer(self):
        table = MemTable(threshold=5)
        table.put("a", "1")
        table.put("a", "2")
        assert table.flush() == [("a", "2")]
