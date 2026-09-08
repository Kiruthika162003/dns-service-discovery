"""Jump consistent hash: no memory, minimal movement, and only one place a bucket may leave.

Jump hash maps a key to one of N buckets with no stored state at
all, just a short loop over a reproducible pseudo-random sequence,
and it moves only about one key in N when the bucket count grows.
That is a remarkable trade against ring-based hashing, which needs
a table of virtual nodes to spread load, but it comes with a
constraint that must be stated rather than discovered. Jump hash
numbers its buckets zero through N minus one, and it can only add
or remove a bucket at the high end of that range: growing from N
to N plus one moves keys only into the new bucket, but there is no
way to remove bucket three from the middle without renumbering
everything above it, because the algorithm's whole economy comes
from never storing which buckets exist. So jump hash fits an
elastic pool that scales at one edge, a shard count that only ever
grows or shrinks from the top, and the module refuses a
middle-bucket removal by name rather than letting a caller assume
an arbitrary node can leave the way it can with rendezvous hashing.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid

_MASK = 0xFFFFFFFFFFFFFFFF


def _key_int(key: str) -> int:
    digest = hashlib.blake2b(key.encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def jump_hash(key: str, num_buckets: int) -> int:
    if num_buckets < 1:
        raise Invalid(
            "jump hash needs at least one bucket; there is no "
            "bucket zero to fall back to otherwise"
        )
    value = _key_int(key)
    bucket = -1
    j = 0
    while j < num_buckets:
        bucket = j
        value = (value * 2862933555777941757 + 1) & _MASK
        j = int((bucket + 1) * (float(1 << 31) / float((value >> 33) + 1)))
    return bucket


def moved_fraction(
    keys: list[str], old_buckets: int, new_buckets: int
) -> float:
    moved = sum(
        1
        for key in keys
        if jump_hash(key, old_buckets) != jump_hash(key, new_buckets)
    )
    return moved / len(keys)


def remove_middle_bucket(index: int, num_buckets: int) -> None:
    if 0 <= index < num_buckets - 1:
        raise Invalid(
            f"bucket {index} is not the last of {num_buckets}; "
            "jump hash can only shed the top bucket, since it "
            "stores no map of which buckets exist to renumber"
        )
