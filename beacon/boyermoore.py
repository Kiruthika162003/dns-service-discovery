"""Boyer-Moore-Horspool search: skip ahead on a mismatch, often reading a fraction of the text.

Naive substring search compares the pattern at every position, but
most positions can be ruled out without checking every character.
Boyer-Moore-Horspool aligns the pattern against the text and compares
from the right end backward, and on a mismatch it consults a
precomputed table to jump the pattern forward by as much as possible:
the character in the text aligned with the pattern's last position
determines the shift, sliding the pattern so that character lines up
with its rightmost occurrence in the pattern, or past it entirely if
it does not appear. Because a single mismatched character can skip a
whole pattern-length ahead, the search often examines far fewer than
every character, running sublinearly on favorable inputs, and it does
best with long patterns over large alphabets where mismatches are
common and skips are large. The costs are the preprocessing to build
the shift table and a worst case that is still the product of the
lengths on adversarial input, unlike a naive scan's simplicity. The
module builds the bad-character shift table, searches right-to-left
with it, and returns the first match index or minus one, refusing an
empty pattern that matches nothing definite.
"""

from __future__ import annotations

from beacon.errors import Invalid


def search(text: str, pattern: str) -> int:
    if pattern == "":
        raise Invalid("an empty pattern matches no definite position")
    m = len(pattern)
    n = len(text)
    if m > n:
        return -1
    shift = {pattern[i]: m - 1 - i for i in range(m - 1)}
    pos = 0
    while pos <= n - m:
        j = m - 1
        while j >= 0 and text[pos + j] == pattern[j]:
            j -= 1
        if j < 0:
            return pos
        pos += shift.get(text[pos + m - 1], m)
    return -1
