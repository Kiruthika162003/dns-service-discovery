"""Move-to-front: turn recently-seen bytes into small numbers for the next stage.

Move-to-front is a transform, not a compressor, and it earns its place
as the middle stage of a pipeline. It keeps an ordered list of all byte
values and, for each input byte, emits that byte's current position in
the list and then moves the byte to the front. When the input has been
arranged so that the same byte recurs in bursts, as the output of a
Burrows-Wheeler transform is, each burst after its first byte emits a
run of zeros, because the repeated byte is already at the front. A
stream dominated by small numbers, especially zeros, is exactly what a
run-length or entropy stage compresses well, so move-to-front converts
locality of reference into numeric skew that the next stage can exploit.
The transform is perfectly reversible: the decoder keeps the same list,
reads each position, recovers the byte there, and moves it to the front
in step. The honest caveat is that move-to-front helps only when the
input already has strong local repetition; applied to data without it,
the positions stay large and the transform can even hurt, which is why
it belongs after a stage that creates that locality rather than on raw
input. This module encodes bytes to a list of positions and decodes
them back.
"""

from __future__ import annotations

from beacon.errors import Invalid


def encode(data: bytes) -> list[int]:
    table = list(range(256))
    positions: list[int] = []
    for byte in data:
        index = table.index(byte)
        positions.append(index)
        table.pop(index)
        table.insert(0, byte)
    return positions


def decode(positions: list[int]) -> bytes:
    table = list(range(256))
    result = bytearray()
    for index in positions:
        if not 0 <= index < 256:
            raise Invalid(
                f"position {index} is outside the range 0 to 255; it cannot "
                "name a byte in the move-to-front table"
            )
        byte = table[index]
        result.append(byte)
        table.pop(index)
        table.insert(0, byte)
    return bytes(result)
