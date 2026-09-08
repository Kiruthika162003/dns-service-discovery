"""Base32: encode binary in 32 case-insensitive characters that survive DNS and human hands.

Binary data sometimes has to travel through a channel that mangles
case or is transcribed by a person, a DNS label, an NSEC3 hash, a
recovery code read aloud, and base64 fails there because it uses both
upper and lower case as distinct symbols and includes characters a
careless channel alters. Base32 trades size for robustness. It maps
each five bits of the input to one of thirty-two characters drawn
from the uppercase letters and the digits two through seven, an
alphabet with no case distinction and no easily confused symbols, so
the encoding is unchanged by case folding and safe in the awkward
channels base64 cannot cross. The cost is expansion: five bits per
character means the output is sixty percent larger than the input,
against base64's thirty-three percent, so base32 is chosen when the
channel demands its robustness and not merely to encode bytes
compactly. Padding with the equals sign fills the final group to a
byte boundary so the length is recoverable. The module encodes bytes
to a base32 string with padding and decodes a base32 string back to
the exact bytes, refusing a character outside the alphabet, which
names no five-bit value.
"""

from __future__ import annotations

from beacon.errors import Invalid

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_LOOKUP = {char: index for index, char in enumerate(_ALPHABET)}


def encode(data: bytes) -> str:
    if not data:
        return ""
    bits = 0
    count = 0
    out: list[str] = []
    for byte in data:
        bits = (bits << 8) | byte
        count += 8
        while count >= 5:
            count -= 5
            out.append(_ALPHABET[(bits >> count) & 0x1F])
    if count:
        out.append(_ALPHABET[(bits << (5 - count)) & 0x1F])
    while len(out) % 8:
        out.append("=")
    return "".join(out)


def decode(text: str) -> bytes:
    stripped = text.rstrip("=").upper()
    bits = 0
    count = 0
    out = bytearray()
    for char in stripped:
        if char not in _LOOKUP:
            raise Invalid(
                f"{char!r} is not a base32 character; it names no "
                "five-bit value"
            )
        bits = (bits << 5) | _LOOKUP[char]
        count += 5
        if count >= 8:
            count -= 8
            out.append((bits >> count) & 0xFF)
    return bytes(out)
