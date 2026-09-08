"""EDNS Client Subnet: a geo-accurate answer bought with a fragmented cache.

An authority that answers by geography needs to know where the
client is, but a recursive resolver stands between them and by
default the authority sees only the resolver's location, so a
user in Tokyo behind a resolver in Frankfurt gets a European
answer. Client Subnet forwards a truncated prefix of the
client's address so the authority can localize, and the honest
cost is twofold. Privacy, because the client's network is now
disclosed to every authority on the path, which is why the
resolver truncates to a prefix rather than sending the full
address. Cache pressure, because a single cached name splinters
into one entry per scope the authority hands back. The guess
that Client Subnet simply makes everyone faster is refuted by
counting: a /24 scope turns one cached A record into as many as
256 distinct entries, so the localized answer is paid for in
cache entries, and a scope of zero is the authority's way of
saying the answer is global and must not be fragmented at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


def truncate(addr: str, prefix: int) -> str:
    parts = addr.split(".")
    if len(parts) != 4:
        raise Invalid(f"{addr} is not a dotted IPv4 address")
    octets = []
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise Invalid(f"{part} is not an octet in {addr}")
        octets.append(int(part))
    if not 0 <= prefix <= 32:
        raise Invalid(
            f"an IPv4 prefix is 0 to 32 bits, not {prefix}"
        )
    value = (
        (octets[0] << 24)
        | (octets[1] << 16)
        | (octets[2] << 8)
        | octets[3]
    )
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix else 0
    value &= mask
    return ".".join(str((value >> shift) & 0xFF) for shift in (24, 16, 8, 0))


@dataclass(frozen=True)
class ScopedAnswer:
    name: str
    client_prefix: int
    scope_prefix: int

    def __post_init__(self) -> None:
        if not 0 <= self.scope_prefix <= 32:
            raise Invalid(
                f"a scope of {self.scope_prefix} bits is outside "
                "the IPv4 range the authority may return"
            )

    def is_global(self) -> bool:
        return self.scope_prefix == 0

    def cache_key(self, client_addr: str) -> tuple[str, str, int]:
        if self.is_global():
            return (self.name, "*", 0)
        scoped = truncate(client_addr, self.scope_prefix)
        return (self.name, scoped, self.scope_prefix)


def entries_under(scope_prefix: int, covering_prefix: int) -> int:
    if scope_prefix < covering_prefix:
        raise Invalid(
            f"a /{scope_prefix} scope is coarser than the "
            f"/{covering_prefix} block it is meant to split, so "
            "it cannot fragment it"
        )
    return 2 ** (scope_prefix - covering_prefix)


def fragmentation_report(scope_prefix: int) -> str:
    if scope_prefix == 0:
        return (
            f"{scope_prefix} scope: global answer, one cache "
            "entry for every client; no fragmentation"
        )
    splits = entries_under(scope_prefix, 0)
    return (
        f"/{scope_prefix} scope: up to {splits} distinct cache "
        "entries per name, the price of the localized answer"
    )
