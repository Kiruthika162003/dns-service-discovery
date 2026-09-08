from __future__ import annotations

import pytest

from beacon.binaryheap import BinaryHeap
from beacon.errors import Invalid


class TestHeapOrder:
    def test_pop_returns_ascending(self):
        heap = BinaryHeap()
        for value in (5, 1, 8, 3, 9, 2):
            heap.push(value)
        popped = [heap.pop() for _ in range(len(heap))]
        assert popped == [1, 2, 3, 5, 8, 9]

    def test_peek_shows_the_minimum_without_removing(self):
        heap = BinaryHeap()
        heap.push(4)
        heap.push(2)
        assert heap.peek() == 2
        assert len(heap) == 2

    def test_interleaved_push_and_pop(self):
        heap = BinaryHeap()
        heap.push(5)
        heap.push(3)
        assert heap.pop() == 3
        heap.push(1)
        heap.push(4)
        assert heap.pop() == 1
        assert heap.pop() == 4
        assert heap.pop() == 5


class TestEmpty:
    def test_popping_empty_is_refused(self):
        with pytest.raises(Invalid):
            BinaryHeap().pop()

    def test_peeking_empty_is_refused(self):
        with pytest.raises(Invalid):
            BinaryHeap().peek()
