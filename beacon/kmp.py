"""Knuth-Morris-Pratt: substring search that never re-examines a text character.

Naive substring search, on a mismatch, slides the pattern one place
and starts comparing again from the beginning, re-examining text
characters it already looked at. Knuth-Morris-Pratt refuses that
wasted work by learning from the pattern itself where a mismatch can
resume. It precomputes a failure function, for each position in the
pattern the length of the longest proper prefix that is also a suffix
ending there, and on a mismatch it uses that to slide the pattern so
the already-matched prefix lines up, without moving the text pointer
backward at all. Because the text pointer only ever advances, the
search reads each text character at most a constant number of times,
giving a guaranteed linear time that neither Boyer-Moore, whose skips
are only an average-case win, nor Rabin-Karp, whose speed rests on a
hash not colliding, can promise in the worst case. The price is the
preprocessing of the failure function, itself linear in the pattern.
The module builds the failure function from the pattern and searches
the text with it, returning the first match index or minus one, and
refusing an empty pattern that matches no definite position.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _failure(pattern: str) -> list[int]:
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def search(text: str, pattern: str) -> int:
    if pattern == "":
        raise Invalid("an empty pattern matches no definite position")
    lps = _failure(pattern)
    i = j = 0
    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == len(pattern):
                return i - j
        elif j:
            j = lps[j - 1]
        else:
            i += 1
    return -1
