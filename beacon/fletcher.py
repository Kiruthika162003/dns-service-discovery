"""Fletcher's checksum: catch transpositions a plain sum misses, cheaper than a CRC.

A plain additive checksum, summing the bytes, catches many errors but
is blind to some obvious ones: swap two bytes and the sum is
unchanged, so a transposition slips through undetected. Fletcher's
checksum fixes that cheaply by carrying two running sums. The first
is the ordinary byte sum, and the second accumulates the first sum at
every step, so it grows faster for bytes seen earlier, giving each
byte a positional weight. Because position now matters, swapping two
bytes changes the second sum and the error is caught, and the two
sums are packed into one checksum word. It is far cheaper than a
cyclic redundancy check, just two additions and a modulus per byte,
which is why lightweight protocols use it, and the honest limit is
that a CRC still catches more, in particular longer burst errors that
Fletcher can miss, so Fletcher is the choice when speed matters more
than the last increment of detection strength. The module computes
the Fletcher-16 checksum over a byte string with the two modular
running sums, and detects that a transposition changes it where a
plain sum would not.
"""

from __future__ import annotations


def fletcher16(data: bytes) -> int:
    sum1 = 0
    sum2 = 0
    for byte in data:
        sum1 = (sum1 + byte) % 255
        sum2 = (sum2 + sum1) % 255
    return (sum2 << 8) | sum1


def plain_sum(data: bytes) -> int:
    return sum(data) % 255
