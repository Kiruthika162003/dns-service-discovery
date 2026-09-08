"""Address sorting: put the address the client can reach cheaply first, keep the rest stable.

When a name resolves to several addresses, the order they are
returned matters, because many clients simply try the first, and
the first should be the one the client can reach best. The oldest
form of this preference is topological: an address on the same
subnet as the client is on-link, reachable without a router hop,
so it belongs at the front, and the classic sortlist behavior
moves same-subnet addresses ahead of the rest. The subtle
requirement is stability. Sorting must not reshuffle the addresses
that share a preference tier, because round-robin rotation and
weighting already arranged them for load spreading, and a sort
that reordered within a tier would silently undo that. So the
module partitions the addresses into on-link and off-link by
comparing each against the client's subnet, preserves the original
order inside each partition, and concatenates, which is a stable
sort by a single boolean key. The result honors locality for the
client that has an on-link option while leaving every other
client, and every within-tier decision the load balancer made,
exactly as it found them.
"""

from __future__ import annotations

from beacon.errors import Invalid


def _truncate(addr: str, prefix: int) -> int:
    parts = addr.split(".")
    if len(parts) != 4:
        raise Invalid(f"{addr} is not a dotted IPv4 address")
    octets = []
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise Invalid(f"{part} is not an octet in {addr}")
        octets.append(int(part))
    value = (
        (octets[0] << 24)
        | (octets[1] << 16)
        | (octets[2] << 8)
        | octets[3]
    )
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0
    return value & mask


def on_link(client: str, addr: str, prefix: int = 24) -> bool:
    if not 0 <= prefix <= 32:
        raise Invalid(f"a prefix of {prefix} is outside 0 to 32")
    return _truncate(client, prefix) == _truncate(addr, prefix)


def sort_addresses(
    client: str, addresses: list[str], prefix: int = 24
) -> list[str]:
    local = [a for a in addresses if on_link(client, a, prefix)]
    remote = [a for a in addresses if not on_link(client, a, prefix)]
    return local + remote
