"""Rabin-Karp: find a pattern by rolling a hash over the text, confirming only on a hash match.

Searching for a pattern in text by comparing it at every position
costs the pattern length at each of many positions, and Rabin-Karp
cuts the common case to constant work per position with a rolling
hash. It hashes the pattern once, hashes the first window of the
text, and then slides the window one character at a time, updating
the hash in constant time by removing the leaving character's
contribution and adding the entering one rather than rehashing the
whole window. Only when a window's hash equals the pattern's hash
does it fall back to a character comparison to confirm, because
different strings can share a hash. On typical text the hashes rarely
collide, so the confirmations are rare and the search runs in
expected linear time, which is why the technique shines for streaming
search and for scanning many patterns at once by comparing against a
set of hashes. The honest caveat is the collision: a pathological or
adversarial text can force a confirming compare at every position and
degrade to the naive cost, and the modulus trades a lower collision
rate against wider arithmetic. The module rolls the hash across the
text and returns the first confirmed match index, or minus one.
"""

from __future__ import annotations

from beacon.errors import Invalid

_BASE = 256
_MOD = 1_000_000_007


def search(text: str, pattern: str) -> int:
    if pattern == "":
        raise Invalid("an empty pattern matches everywhere and nowhere")
    n, m = len(text), len(pattern)
    if m > n:
        return -1
    high = pow(_BASE, m - 1, _MOD)
    pattern_hash = 0
    window_hash = 0
    for i in range(m):
        pattern_hash = (pattern_hash * _BASE + ord(pattern[i])) % _MOD
        window_hash = (window_hash * _BASE + ord(text[i])) % _MOD
    for start in range(n - m + 1):
        if window_hash == pattern_hash and text[start : start + m] == pattern:
            return start
        if start < n - m:
            window_hash = (
                (window_hash - ord(text[start]) * high) * _BASE
                + ord(text[start + m])
            ) % _MOD
    return -1
