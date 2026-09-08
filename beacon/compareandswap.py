"""Compare-and-swap and the ABA problem: why plain CAS is fooled by a value that came back.

Compare-and-swap is the atomic primitive lock-free algorithms are
built on: it sets a cell to a new value only if the cell currently
holds the value the caller expected, and it reports whether it
succeeded, so a thread can read a value, compute a new one, and
install it only if no one changed it in between. The subtlety that
breaks naive uses is the ABA problem. A CAS checks only the value,
not its history, so if the cell went from A to B and back to A while
the caller was working, the caller's CAS expecting A succeeds as
though nothing happened, even though the value was modified twice and
whatever those modifications meant is lost. This bites hardest with
reused memory, a freed and reallocated node whose pointer returns to
its old address, where the CAS wrongly concludes the structure is
unchanged. The fix is a version stamp: pair the value with a counter
that increments on every change, and CAS on the pair, so a value that
returns to A carries a different stamp and the stale CAS correctly
fails. The module offers a plain CAS that exhibits the ABA hazard and
a stamped CAS that closes it, so the difference between checking a
value and checking its history is concrete.
"""

from __future__ import annotations


class AtomicCell:
    def __init__(self, value: str) -> None:
        self.value = value
        self.stamp = 0

    def cas(self, expected: str, new: str) -> bool:
        if self.value == expected:
            self.value = new
            self.stamp += 1
            return True
        return False

    def stamped_cas(
        self, expected: str, expected_stamp: int, new: str
    ) -> bool:
        if self.value == expected and self.stamp == expected_stamp:
            self.value = new
            self.stamp += 1
            return True
        return False
