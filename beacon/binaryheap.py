"""A binary min-heap: the smallest element always at hand, insert and extract in log time.

A priority queue needs the smallest, or largest, element quickly
while items are added and removed continually, and a sorted list
gives instant access but linear insertion, while an unsorted list
gives instant insertion but linear access. A binary heap balances
both. It is a complete binary tree kept in an array, where every
parent is no greater than its children, so the minimum is always at
the root, index zero, available in constant time. Inserting appends
at the end and sifts the new element up, swapping it past larger
parents until the heap order is restored, and extracting the minimum
moves the last element to the root and sifts it down past its smaller
child until order returns, each touching only the height of the tree,
which is logarithmic. That makes the heap the structure behind
event schedulers, Dijkstra's frontier, and any repeated
extract-the-extreme workload. The module pushes with a sift-up,
pops the minimum with a sift-down, peeks the minimum without
removing it, and refuses to pop or peek an empty heap, since there is
no minimum of nothing.
"""

from __future__ import annotations

from beacon.errors import Invalid


class BinaryHeap:
    def __init__(self) -> None:
        self.data: list[int] = []

    def push(self, value: int) -> None:
        self.data.append(value)
        child = len(self.data) - 1
        while child > 0:
            parent = (child - 1) // 2
            if self.data[parent] <= self.data[child]:
                break
            self.data[parent], self.data[child] = (
                self.data[child],
                self.data[parent],
            )
            child = parent

    def peek(self) -> int:
        if not self.data:
            raise Invalid("an empty heap has no minimum")
        return self.data[0]

    def pop(self) -> int:
        if not self.data:
            raise Invalid("an empty heap has nothing to pop")
        top = self.data[0]
        last = self.data.pop()
        if self.data:
            self.data[0] = last
            self._sift_down(0)
        return top

    def _sift_down(self, index: int) -> None:
        size = len(self.data)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < size and self.data[left] < self.data[smallest]:
                smallest = left
            if right < size and self.data[right] < self.data[smallest]:
                smallest = right
            if smallest == index:
                return
            self.data[index], self.data[smallest] = (
                self.data[smallest],
                self.data[index],
            )
            index = smallest

    def __len__(self) -> int:
        return len(self.data)
