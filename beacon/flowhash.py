"""Flow hashing for ECMP: keep a connection's packets on one path so they never reorder.

When several equal-cost paths lead to a destination, spreading
traffic across them is good for utilization but dangerous per
connection, because if a single connection's packets take different
paths they can arrive out of order, which the receiver mistakes for
loss and which wrecks throughput. Flow hashing resolves the tension.
It hashes the flow's five-tuple, source and destination address,
source and destination port, and protocol, to pick a path, so every
packet of one connection, sharing that tuple, hashes to the same path
and stays in order, while different connections hash to different
paths and spread across the links. The honest limit the module names
is that this balances flows, not bytes. Every flow is one hash,
regardless of how much data it carries, so a single very large flow,
an elephant, is pinned to one path and can saturate it while other
paths sit idle, since the hash cannot split a flow without
reordering it. Mitigating that needs flow-size awareness on top,
which is why elephant-flow detection exists. The module hashes a
five-tuple to a path index and decides whether two flows share a
path, so the in-order guarantee and the flow-not-byte balancing are
both explicit.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def flow_path(five_tuple: tuple[str, str, int, int, str], num_paths: int) -> int:
    if num_paths < 1:
        raise Invalid("there must be at least one path to hash onto")
    key = "|".join(str(part) for part in five_tuple)
    digest = hashlib.blake2b(key.encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big") % num_paths


def same_path(
    a: tuple[str, str, int, int, str],
    b: tuple[str, str, int, int, str],
    num_paths: int,
) -> bool:
    return flow_path(a, num_paths) == flow_path(b, num_paths)
