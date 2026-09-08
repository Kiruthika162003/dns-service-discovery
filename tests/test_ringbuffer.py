from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ringbuffer import RingBuffer


class TestPush:
    def test_it_fills_without_eviction(self):
        ring = RingBuffer(capacity=3)
        assert ring.push("a") is None
        assert ring.push("b") is None
        assert not ring.is_full() or ring.contents() == ["a", "b"]

    def test_a_full_buffer_evicts_the_oldest(self):
        ring = RingBuffer(capacity=3)
        for item in ("a", "b", "c"):
            ring.push(item)
        assert ring.is_full()
        assert ring.push("d") == "a"
        assert ring.contents() == ["b", "c", "d"]


class TestContents:
    def test_contents_run_oldest_to_newest_after_wrap(self):
        ring = RingBuffer(capacity=3)
        for item in ("a", "b", "c", "d", "e"):
            ring.push(item)
        assert ring.contents() == ["c", "d", "e"]


class TestConstruction:
    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            RingBuffer(0)
