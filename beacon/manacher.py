"""Manacher's algorithm: the longest palindromic substring in linear time.

The obvious way to find the longest palindrome in a string is to try
expanding around every center, which is quadratic because each center's
expansion redoes work its neighbors already proved. Manacher's algorithm
removes that waste and runs in linear time. It first transforms the
string by inserting a separator between every character and at both
ends, which folds the awkward distinction between odd-length and
even-length palindromes into a single uniform case where every
palindrome has a real center. Then it sweeps left to right computing, at
each center, the radius of the palindrome there, and it reuses earlier
work exactly as the Z-algorithm does: it tracks the palindrome that
currently reaches furthest right, and for a new center inside that reach
it seeds the radius from the mirror center's already-known value before
expanding further, so the right boundary only advances. The result is
the whole longest palindromic substring recovered from the widest radius
found. The honest note is scope: the algorithm is specialized to
contiguous palindromic substrings and does not generalize to
subsequences or to approximate palindromes, which need dynamic
programming instead. This module returns the longest palindromic
substring, choosing the earliest when several tie.
"""

from __future__ import annotations


def longest_palindrome(text: str) -> str:
    if text == "":
        return ""
    transformed = "^#" + "#".join(text) + "#$"
    n = len(transformed)
    radius = [0] * n
    center = right = 0
    for i in range(1, n - 1):
        if i < right:
            radius[i] = min(right - i, radius[2 * center - i])
        while transformed[i + radius[i] + 1] == transformed[i - radius[i] - 1]:
            radius[i] += 1
        if i + radius[i] > right:
            center, right = i, i + radius[i]
    best_length = max(radius)
    best_center = radius.index(best_length)
    start = (best_center - best_length) // 2
    return text[start : start + best_length]
