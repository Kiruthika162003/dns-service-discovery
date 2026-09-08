"""A monotonic-deque sliding maximum: the window's max in amortized constant time.

Tracking the maximum over a sliding window of a stream, the peak
request rate in the last minute, the worst latency in the last
hundred samples, is O(k) per step if the max is recomputed over the
window each time. A monotonic deque brings it to amortized constant
time by keeping only the values that could still become the maximum.
The deque holds indices whose values decrease from front to back, and
on a new value every smaller value at the back is discarded first,
because a later, larger value dominates them, no earlier smaller value
can ever be the max again while the newcomer is in the window. The
new value is appended, and the front is dropped if it has aged out of
the window, so the front of the deque is always the current window's
maximum. Each value is pushed and popped at most once, giving the
amortized constant cost, and the deque holds only the descending
staircase of candidates rather than the whole window. The module
pushes a value at an index, evicts indices that fall outside the
window and dominated values from the back, and reports the current
maximum from the front, refusing a query before any value is in the
window.
"""

from __future__ import annotations

from collections import deque

from beacon.errors import Invalid


class SlidingMax:
    def __init__(self, window: int) -> None:
        if window < 1:
            raise Invalid("a window of zero holds no values to maximize")
        self.window = window
        self.deque: deque[tuple[int, float]] = deque()

    def push(self, index: int, value: float) -> None:
        while self.deque and self.deque[-1][1] <= value:
            self.deque.pop()
        self.deque.append((index, value))
        while self.deque and self.deque[0][0] <= index - self.window:
            self.deque.popleft()

    def maximum(self) -> float:
        if not self.deque:
            raise Invalid("no value in the window to take a maximum of")
        return self.deque[0][1]
