"""Z-algorithm: for every position, how far it matches the string's own prefix.

The Z-array of a string records, at each position, the length of the
longest substring starting there that is also a prefix of the whole
string. That single table answers a surprising range of questions in
linear time, most directly exact pattern matching: glue the pattern, a
separator that appears in neither, and the text into one string, and
every position in the text part whose Z-value reaches the pattern's
length marks an occurrence. What makes it linear rather than quadratic
is that it never rescans matched characters. It maintains the rightmost
match interval it has discovered so far, and when it reaches a new
position already inside that interval it copies the answer from the
mirror position that a prior match guarantees, extending by explicit
comparison only past the interval's edge, so the right edge only ever
moves forward. The honest tradeoff against a method like KMP is
conceptual, not asymptotic: both are linear, but the Z-array is a
general-purpose measurement of self-similarity that pattern matching
merely borrows, where KMP's failure function is purpose-built for the
match. This module computes the Z-array and uses it to find every
occurrence of a pattern in a text. It refuses a separator that occurs
in the inputs, since that would corrupt the concatenation.
"""

from __future__ import annotations

from beacon.errors import Invalid

_SEPARATOR = "\x00"


def z_array(text: str) -> list[int]:
    n = len(text)
    z = [0] * n
    if n == 0:
        return z
    z[0] = n
    left = right = 0
    for i in range(1, n):
        if i < right:
            z[i] = min(right - i, z[i - left])
        while i + z[i] < n and text[z[i]] == text[i + z[i]]:
            z[i] += 1
        if i + z[i] > right:
            left, right = i, i + z[i]
    return z


def search(text: str, pattern: str) -> list[int]:
    if pattern == "":
        return list(range(len(text) + 1))
    if _SEPARATOR in text or _SEPARATOR in pattern:
        raise Invalid(
            "the text or pattern contains the reserved separator byte; this "
            "search needs a byte that appears in neither input"
        )
    combined = pattern + _SEPARATOR + text
    z = z_array(combined)
    span = len(pattern)
    matches: list[int] = []
    for i in range(span + 1, len(combined)):
        if z[i] >= span:
            matches.append(i - span - 1)
    return matches
