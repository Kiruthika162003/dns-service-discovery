"""A monotonic stack: the next greater element for every position, in one linear pass.

For each value in a sequence, finding the next value to its right
that is larger, the next spike above a reading, the next taller bar,
is quadratic if done by scanning forward from every position, and a
monotonic stack brings it to linear. It walks the sequence once,
keeping a stack of positions whose next-greater element has not yet
been found, and the stack is kept monotonic, its values decreasing
from bottom to top. When a new value arrives, it is greater than
whatever sits on top of the stack while those tops are smaller, so
each such top has just found its next-greater element, the new value,
and is popped and answered; the new position is then pushed to wait
for its own. Because every position is pushed once and popped at most
once, the whole pass is linear despite the inner popping, the classic
amortized argument. Positions still on the stack at the end have no
greater element to their right and are answered with a sentinel. The
same structure, flipped, finds next-smaller elements, and it
underlies stock-span and largest-rectangle problems. The module
returns, for each position, the next strictly greater value to its
right or minus one when none exists.
"""

from __future__ import annotations


def next_greater(values: list[int]) -> list[int]:
    result = [-1] * len(values)
    stack: list[int] = []
    for index, value in enumerate(values):
        while stack and values[stack[-1]] < value:
            result[stack.pop()] = value
        stack.append(index)
    return result
