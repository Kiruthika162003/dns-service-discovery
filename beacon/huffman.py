"""Huffman coding: give frequent symbols short codes, the optimal per-symbol prefix code.

Compressing a stream of symbols to fewer bits than a fixed-width
encoding means spending fewer bits on the symbols that occur often
and more on the rare ones, and Huffman coding finds the best such
assignment for a known frequency distribution. It repeatedly takes
the two least-frequent symbols or subtrees and merges them under a
new parent whose frequency is their sum, so the least-frequent
symbols end up deepest in the resulting tree and thus get the longest
codes, and the most frequent end up shallow with the shortest. Each
symbol's code is the path from the root to its leaf, and because every
symbol is a leaf, no code is a prefix of another, which is what lets a
decoder read the bitstream unambiguously with no separators. The
result is provably optimal among codes that assign a whole number of
bits to each symbol. Its limit, honestly, is exactly that
whole-number constraint: a symbol whose ideal code length is
fractional must round to a whole bit, wasting a little, which is why
arithmetic coding, unbounded by bit boundaries, can do better on
skewed distributions. The module builds the code table from symbol
frequencies, encodes a message to a bitstring and decodes it back,
handling the single-symbol alphabet that would otherwise have a
zero-length code.
"""

from __future__ import annotations

import heapq

from beacon.errors import Invalid


def build_codes(frequencies: dict[str, int]) -> dict[str, str]:
    if not frequencies:
        raise Invalid("no symbols to build a code from")
    if len(frequencies) == 1:
        symbol = next(iter(frequencies))
        return {symbol: "0"}
    heap: list[tuple[int, int, dict[str, str]]] = []
    counter = 0
    for symbol, freq in frequencies.items():
        heapq.heappush(heap, (freq, counter, {symbol: ""}))
        counter += 1
    while len(heap) > 1:
        freq_a, _, codes_a = heapq.heappop(heap)
        freq_b, _, codes_b = heapq.heappop(heap)
        merged = {}
        for symbol, code in codes_a.items():
            merged[symbol] = "0" + code
        for symbol, code in codes_b.items():
            merged[symbol] = "1" + code
        heapq.heappush(heap, (freq_a + freq_b, counter, merged))
        counter += 1
    return heap[0][2]


def encode(message: str, codes: dict[str, str]) -> str:
    bits = []
    for symbol in message:
        if symbol not in codes:
            raise Invalid(f"{symbol!r} has no code in the table")
        bits.append(codes[symbol])
    return "".join(bits)


def decode(bitstring: str, codes: dict[str, str]) -> str:
    inverse = {code: symbol for symbol, code in codes.items()}
    result = []
    current = ""
    for bit in bitstring:
        current += bit
        if current in inverse:
            result.append(inverse[current])
            current = ""
    if current:
        raise Invalid(
            "the bitstring ends mid-code; it is truncated or was not "
            "produced by this code table"
        )
    return "".join(result)
