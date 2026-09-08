"""A cuckoo filter: set membership with deletion, storing fingerprints in two candidate buckets.

A cuckoo filter is a membership structure that, unlike a Bloom
filter, supports deletion, and at low false-positive rates uses less
space. It stores a short fingerprint of each item, not the item, in
one of two candidate buckets. The first bucket comes from hashing the
item, the second from the first XORed with a hash of the fingerprint,
an involution so that from either bucket and the fingerprint the
other bucket is recoverable, which is what makes deletion and
relocation possible without the original item. Insertion places the
fingerprint in whichever candidate bucket has room, and if both are
full it evicts a resident and relocates it to its own alternate
bucket, cascading these cuckoo kicks until everyone has a home or a
kick limit is hit. Deletion simply removes the fingerprint from
either candidate bucket. Membership checks both buckets for the
fingerprint. The honest cost the module surfaces is that insertion
can fail: when the table is too full the relocation chain exhausts
and the insert is refused, a full signal a Bloom filter never gives,
since it just grows more false-positive. The module requires a
power-of-two bucket count so the XOR-based alternate is a true
involution, and it adds, tests, and deletes fingerprints.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _hash(data: str) -> int:
    return int.from_bytes(
        hashlib.blake2b(data.encode(), digest_size=8).digest(), "big"
    )


class CuckooFilter:
    def __init__(
        self, num_buckets: int, bucket_size: int = 4, max_kicks: int = 500
    ) -> None:
        if num_buckets < 1 or (num_buckets & (num_buckets - 1)) != 0:
            raise Invalid(
                "the bucket count must be a power of two so the "
                "XOR-based alternate bucket is a true involution"
            )
        self.mask = num_buckets - 1
        self.bucket_size = bucket_size
        self.max_kicks = max_kicks
        self.buckets: list[list[int]] = [[] for _ in range(num_buckets)]

    def _fingerprint(self, item: str) -> int:
        return (_hash("fp:" + item) & 0xFF) or 1

    def _index(self, item: str) -> int:
        return _hash("idx:" + item) & self.mask

    def _alt(self, index: int, fingerprint: int) -> int:
        return (index ^ (_hash(f"fp:{fingerprint}") & self.mask)) & self.mask

    def add(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        i1 = self._index(item)
        i2 = self._alt(i1, fingerprint)
        for index in (i1, i2):
            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(fingerprint)
                return True
        index = i1
        for _ in range(self.max_kicks):
            victim = self.buckets[index][0]
            self.buckets[index][0] = fingerprint
            fingerprint = victim
            index = self._alt(index, fingerprint)
            if len(self.buckets[index]) < self.bucket_size:
                self.buckets[index].append(fingerprint)
                return True
        return False

    def contains(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        i1 = self._index(item)
        i2 = self._alt(i1, fingerprint)
        return fingerprint in self.buckets[i1] or fingerprint in self.buckets[i2]

    def delete(self, item: str) -> bool:
        fingerprint = self._fingerprint(item)
        i1 = self._index(item)
        i2 = self._alt(i1, fingerprint)
        for index in (i1, i2):
            if fingerprint in self.buckets[index]:
                self.buckets[index].remove(fingerprint)
                return True
        return False
