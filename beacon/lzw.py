"""LZW compression: build the dictionary from the data itself, so no model is shipped.

LZW compresses by learning the data's own repeated substrings as it
reads, needing neither a frequency model like Huffman nor a second
pass. It starts with a dictionary of every single byte, then scans
the input extending a current string as long as it stays in the
dictionary; when the next byte would leave the dictionary, it emits
the code for the current string, adds the extended string as a new
entry with the next code, and restarts from that byte. So each time a
substring recurs it can be matched by an ever-longer dictionary entry,
and long repeats collapse to single codes. The decompressor is the
elegant half: it rebuilds the exact same dictionary from the codes
alone, in lockstep, because each new entry is determined by the codes
already seen, so nothing about the dictionary needs to be
transmitted. There is one famous subtlety, a code that refers to an
entry defined on the very same step, which the decompressor handles
by a special case, and the module handles it too. LZW shines on
repetitive data and does almost nothing on random data, and a real
implementation bounds or resets the dictionary when it fills. The
module compresses bytes to a list of codes and decompresses codes
back to the exact bytes, refusing a code that is neither known nor the
next to be defined.
"""

from __future__ import annotations

from beacon.errors import Invalid


def compress(data: bytes) -> list[int]:
    table: dict[bytes, int] = {bytes([i]): i for i in range(256)}
    next_code = 256
    result: list[int] = []
    current = b""
    for byte in data:
        extended = current + bytes([byte])
        if extended in table:
            current = extended
        else:
            result.append(table[current])
            table[extended] = next_code
            next_code += 1
            current = bytes([byte])
    if current:
        result.append(table[current])
    return result


def decompress(codes: list[int]) -> bytes:
    if not codes:
        return b""
    table: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    next_code = 256
    if codes[0] not in table:
        raise Invalid(
            f"the first code {codes[0]} is not a known single byte; the "
            "stream cannot begin with a dictionary entry not yet defined"
        )
    previous = table[codes[0]]
    pieces = [previous]
    for code in codes[1:]:
        if code in table:
            entry = table[code]
        elif code == next_code:
            entry = previous + previous[:1]
        else:
            raise Invalid(
                f"code {code} is neither in the dictionary nor the "
                "next to be defined; the stream is corrupt"
            )
        pieces.append(entry)
        table[next_code] = previous + entry[:1]
        next_code += 1
        previous = entry
    return b"".join(pieces)
