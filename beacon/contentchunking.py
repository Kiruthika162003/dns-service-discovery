"""Content-defined chunking: put chunk boundaries where the data says, so an edit shifts little.

Deduplicating data by splitting it into chunks and storing each
unique chunk once only works if the same content produces the same
chunks, and fixed-size chunking breaks that the moment a byte is
inserted: every chunk after the insertion shifts, its contents change,
and dedup finds nothing in common though almost everything is
unchanged. Content-defined chunking fixes it by choosing boundaries
from the content rather than the offset. A rolling hash runs over a
sliding window of the data, and a boundary is placed wherever that
hash meets a condition, its low bits all zero against a mask, so the
boundary sits at a spot determined by the surrounding bytes. Insert
data anywhere and only the chunks straddling the insertion change; the
boundaries before and after fall on the same content as before, so
dedup still recognizes every unchanged chunk. The cost is variable
chunk sizes, since boundaries appear where the content dictates, and a
rolling hash computed over every byte. The mask sets the average chunk
size, a larger mask meaning rarer boundaries and bigger chunks. The
module rolls the hash and returns the boundary offsets, so the shift-
resistant cutting is concrete rather than asserted.
"""

from __future__ import annotations

from beacon.errors import Invalid

_BASE = 257
_MOD = 1_000_000_007


def boundaries(data: bytes, window: int, mask: int) -> list[int]:
    if window < 1:
        raise Invalid("the rolling window must be at least one byte")
    if mask < 1:
        raise Invalid(
            "a mask of zero matches every position, cutting a chunk "
            "per byte, which is not chunking"
        )
    cuts = []
    if len(data) < window:
        return cuts
    high = pow(_BASE, window - 1, _MOD)
    rolling = 0
    for i in range(window):
        rolling = (rolling * _BASE + data[i]) % _MOD
    for end in range(window, len(data) + 1):
        if rolling & mask == 0:
            cuts.append(end)
        if end < len(data):
            rolling = (
                (rolling - data[end - window] * high) * _BASE + data[end]
            ) % _MOD
    return cuts
