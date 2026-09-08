"""MinHash: estimate how similar two sets are from small fixed-size signatures.

Comparing two large sets for similarity by intersecting them costs
time proportional to their size, which is hopeless when there are
many sets to compare pairwise, as in near-duplicate detection.
MinHash reduces each set to a short signature and estimates the
Jaccard similarity, the size of the intersection over the union, from
the signatures alone. The trick rests on a fact about hashing: if you
hash every element of a set and take the minimum, the probability
that two sets share the same minimum equals their Jaccard similarity,
because the element that hashes smallest across the union is equally
likely to land in the intersection as the similarity dictates. Using
many independent hash functions gives a signature of many minimums,
and the fraction of signature slots that match estimates the
similarity, with an error that shrinks as more hash functions are
added. So two sets of any size are compared by comparing their
fixed-length signatures, cheap and constant per comparison. The
honest cost is that it is an estimate, accurate to about one over the
square root of the signature length, so more accuracy means longer
signatures. The module builds a signature from a set and a hash
count, and estimates similarity as the fraction of matching slots,
refusing a comparison of signatures built with different counts.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def signature(items: set[str], num_hashes: int) -> list[int]:
    if num_hashes < 1:
        raise Invalid("a signature needs at least one hash function")
    if not items:
        raise Invalid("an empty set has no minimum to hash")
    sig = []
    for seed in range(num_hashes):
        minimum = min(
            int.from_bytes(
                hashlib.blake2b(
                    f"{seed}:{item}".encode(), digest_size=8
                ).digest(),
                "big",
            )
            for item in items
        )
        sig.append(minimum)
    return sig


def similarity(sig_a: list[int], sig_b: list[int]) -> float:
    if len(sig_a) != len(sig_b):
        raise Invalid(
            "signatures of different lengths were built with "
            "different hash counts and cannot be compared"
        )
    if not sig_a:
        raise Invalid("empty signatures compare nothing")
    matches = sum(1 for a, b in zip(sig_a, sig_b, strict=True) if a == b)
    return matches / len(sig_a)
