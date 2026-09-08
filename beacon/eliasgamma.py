"""Elias gamma coding: a self-delimiting code for integers of unknown size.

A stream of positive integers whose magnitudes are unknown in advance
cannot use a fixed-width field without either overflowing on the large
values or wasting space on the small ones. Elias gamma coding solves
this with a code that carries its own length. To encode a number it
writes the number in binary, notes that this takes some number of
bits, and prefixes that many zeros followed by the binary itself; the
leading zeros tell the decoder exactly how many bits of value follow,
so no separators are needed and the codes concatenate unambiguously.
Small numbers get short codes and large ones grow only logarithmically,
which suits data dominated by small values, such as gaps between sorted
document identifiers in a search index. The honest tradeoff is the
domain: the code has no representation for zero and none for negative
numbers, so a stream that needs those must shift or interleave them
first. This module encodes a list of positive integers to a bitstring
and decodes the bitstring back, refusing any value below one.
"""

from __future__ import annotations

from beacon.errors import Invalid


def encode(values: list[int]) -> str:
    bits: list[str] = []
    for value in values:
        if value < 1:
            raise Invalid(
                f"cannot Elias-gamma-encode {value}; the code represents only "
                "the positive integers, so shift the data if it includes zero"
            )
        binary = bin(value)[2:]
        bits.append("0" * (len(binary) - 1))
        bits.append(binary)
    return "".join(bits)


def decode(bits: str) -> list[int]:
    values: list[int] = []
    index = 0
    length = len(bits)
    while index < length:
        zeros = 0
        while index < length and bits[index] == "0":
            zeros += 1
            index += 1
        if index >= length:
            raise Invalid(
                "the bitstring ends inside a length prefix; it is truncated "
                "or was not produced by this code"
            )
        end = index + zeros + 1
        if end > length:
            raise Invalid(
                "the bitstring ends inside a value field; it is truncated or "
                "was not produced by this code"
            )
        values.append(int(bits[index:end], 2))
        index = end
    return values
