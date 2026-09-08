"""HyperLogLog: count how many distinct names were queried, in kilobytes, not gigabytes.

Counting the number of distinct clients or distinct names in a
stream exactly needs memory proportional to that number, a set of
everything seen, which is hopeless at internet scale. HyperLogLog
estimates the cardinality in a fixed and tiny amount of memory by
exploiting a fact about random hashes: in a stream of hashed values,
the more distinct values there are, the more likely it is that one
of them began with a long run of leading zeros, since a run of k
zeros appears about once in two-to-the-k draws. The sketch hashes
each item, uses the first few bits to pick one of many registers,
and stores in each register the longest leading-zero run it has
seen, then combines the registers with a harmonic mean to turn the
maximum runs into a cardinality estimate. The result is an estimate,
not a count, with a relative error that shrinks as the square root
of the register count, so a few kilobytes of registers count
billions of distinct items within a percent or two. The module
implements the registers, the leading-zero rank, and the estimator
with the small-cardinality correction that keeps it accurate when
few items have been seen, so the memory-for-precision trade is real
and bounded.
"""

from __future__ import annotations

import hashlib
import math

from beacon.errors import Invalid


class HyperLogLog:
    def __init__(self, precision: int = 12) -> None:
        if not 4 <= precision <= 16:
            raise Invalid(
                f"a precision of {precision} is outside 4 to 16; too "
                "few registers is imprecise and too many wastes the "
                "memory the sketch exists to save"
            )
        self.precision = precision
        self.m = 1 << precision
        self.registers = [0] * self.m
        self.alpha = 0.7213 / (1 + 1.079 / self.m)

    def _hash(self, item: str) -> int:
        return int.from_bytes(
            hashlib.blake2b(str(item).encode(), digest_size=8).digest(),
            "big",
        )

    def add(self, item: str) -> None:
        value = self._hash(item)
        bucket = value >> (64 - self.precision)
        remainder = value & ((1 << (64 - self.precision)) - 1)
        rank = self._leading_zero_rank(remainder, 64 - self.precision)
        self.registers[bucket] = max(self.registers[bucket], rank)

    def _leading_zero_rank(self, remainder: int, width: int) -> int:
        if remainder == 0:
            return width + 1
        return width - remainder.bit_length() + 1

    def estimate(self) -> float:
        harmonic = sum(2.0**-r for r in self.registers)
        raw = self.alpha * self.m * self.m / harmonic
        if raw <= 2.5 * self.m:
            empty = self.registers.count(0)
            if empty > 0:
                return self.m * math.log(self.m / empty)
        return raw
