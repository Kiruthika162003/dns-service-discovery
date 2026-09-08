"""SimHash: a hash where similar inputs land near each other, so near-duplicates are close bits.

A cryptographic hash is built to scatter: change one bit of the input
and the whole output changes, which is exactly wrong for finding
near-duplicates, since two almost-identical documents get two totally
unrelated hashes. SimHash is a locality-sensitive hash built to do
the opposite, to map similar inputs to similar outputs. It hashes
each feature of an input to a bit pattern and, across all features,
tallies each bit position, adding one when a feature's bit is set and
subtracting one when it is clear, then takes the sign of each tally
to form the final hash: a bit is one where the features leaned toward
one. Because the hash is a vote over features, two inputs sharing most
features vote the same way on most bits and so differ in only a few,
and the Hamming distance between two SimHashes, the number of
differing bits, measures how dissimilar the inputs are. Near-duplicate
detection then reduces to finding hashes within a small Hamming
distance. The threshold is the dial: a larger allowed distance catches
looser near-duplicates at the risk of false matches, a smaller one is
stricter. The module computes the SimHash of a feature set, the
Hamming distance between two, and whether two are near-duplicates
under a distance threshold.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid

_BITS = 64


def simhash(features: list[str]) -> int:
    if not features:
        raise Invalid("no features to hash; an empty input has no SimHash")
    tallies = [0] * _BITS
    for feature in features:
        digest = int.from_bytes(
            hashlib.blake2b(feature.encode(), digest_size=8).digest(), "big"
        )
        for bit in range(_BITS):
            if (digest >> bit) & 1:
                tallies[bit] += 1
            else:
                tallies[bit] -= 1
    value = 0
    for bit in range(_BITS):
        if tallies[bit] > 0:
            value |= 1 << bit
    return value


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def near_duplicate(a: int, b: int, threshold: int = 3) -> bool:
    if threshold < 0:
        raise Invalid("a Hamming threshold is never negative")
    return hamming(a, b) <= threshold
