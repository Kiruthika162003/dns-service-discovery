"""DNS64: synthesize an IPv6 answer from an IPv4 one, but never over a real AAAA.

An IPv6-only client cannot reach an IPv4-only server on its own,
so a NAT64 gateway translates between them and DNS64 is the half
that makes the translation findable: when a name has an A record
but no AAAA, the resolver synthesizes an AAAA by embedding the
IPv4 address into a well-known IPv6 prefix, and the client
connects to that synthetic address, which the gateway unpacks
back to the IPv4 host. The rule that keeps DNS64 from breaking
working IPv6 is that synthesis happens only in the absence of a
native AAAA: if the name already answers with real IPv6, that
answer is returned untouched, because synthesizing over it would
route a client through a translator it never needed and could
strand it if the gateway is down while the native path was fine.
The module embeds the address into the prefix, refuses to
synthesize when there is nothing to synthesize from, and refuses
to synthesize when a native AAAA already exists, so the fallback
never shadows the real thing.
"""

from __future__ import annotations

from beacon.errors import Invalid, NoData

WELL_KNOWN_PREFIX = "64:ff9b::"


def synthesize_one(ipv4: str, prefix: str = WELL_KNOWN_PREFIX) -> str:
    parts = ipv4.split(".")
    if len(parts) != 4:
        raise Invalid(f"{ipv4} is not a dotted IPv4 address")
    octets = []
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise Invalid(f"{part} is not an octet in {ipv4}")
        octets.append(int(part))
    high = f"{octets[0]:02x}{octets[1]:02x}"
    low = f"{octets[2]:02x}{octets[3]:02x}"
    return f"{prefix}{high}:{low}"


def dns64_answer(
    native_aaaa: list[str],
    native_a: list[str],
    prefix: str = WELL_KNOWN_PREFIX,
) -> list[str]:
    if native_aaaa:
        raise Invalid(
            "a native AAAA exists; synthesizing over it would "
            "route the client through a translator it does not "
            "need and could strand it if the gateway is down"
        )
    if not native_a:
        raise NoData(
            "no A record to synthesize from; DNS64 makes an IPv6 "
            "answer out of an IPv4 one, and there is no IPv4 one"
        )
    return [synthesize_one(address, prefix) for address in native_a]


def was_synthesized(aaaa: str, prefix: str = WELL_KNOWN_PREFIX) -> bool:
    return aaaa.startswith(prefix)
