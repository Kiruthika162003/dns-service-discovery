"""CIDR ranges: the prefix math that ACLs get wrong in exactly two ways.

Access rules are written in CIDR, 10.0.0.0/8 and
192.168.1.0/24, and two mistakes recur so often they are worth
detecting mechanically. The first is the host-bits-set error:
writing 10.0.0.5/8 when 10.0.0.0/8 was meant, which most tools
silently normalize, hiding a typo that might have meant a
different range entirely. The second is the overlap nobody
noticed: two rules whose ranges intersect, so one shadows part
of the other and the effective policy is not what either rule's
author believed. This module does the prefix arithmetic
exactly on 32-bit integers, refuses a CIDR with host bits set
rather than silently fixing it, and reports overlaps between a
rule set as containment or partial intersection, because an
ACL whose rules overlap is an ACL whose behavior depends on
evaluation order, and order-dependent security should at least
know its own overlaps.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


def _parse_cidr(cidr: str) -> tuple[int, int]:
    if "/" not in cidr:
        raise Invalid(f"{cidr} has no prefix length")
    address, bits_text = cidr.split("/")
    if not bits_text.isdigit():
        raise Invalid(f"{cidr}: prefix length is not a number")
    bits = int(bits_text)
    if not 0 <= bits <= 32:
        raise Invalid(f"{cidr}: prefix must be 0 to 32")
    octets = address.split(".")
    if len(octets) != 4 or not all(
        o.isdigit() and 0 <= int(o) <= 255 for o in octets
    ):
        raise Invalid(f"{cidr}: not a dotted quad")
    value = 0
    for octet in octets:
        value = (value << 8) | int(octet)
    mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
    if value & ~mask:
        raise Invalid(
            f"{cidr} has host bits set; you wrote a host "
            "address where a network was meant, and silently "
            "normalizing it would hide a typo for another range"
        )
    return value, bits


@dataclass(frozen=True)
class CidrRange:
    cidr: str

    def bounds(self) -> tuple[int, int]:
        value, bits = _parse_cidr(self.cidr)
        size = 1 << (32 - bits)
        return value, value + size - 1

    def contains(self, other: CidrRange) -> bool:
        low, high = self.bounds()
        other_low, other_high = other.bounds()
        return low <= other_low and other_high <= high

    def overlaps(self, other: CidrRange) -> bool:
        low, high = self.bounds()
        other_low, other_high = other.bounds()
        return low <= other_high and other_low <= high


def overlap_report(cidrs: list[str]) -> str:
    ranges = [CidrRange(cidr) for cidr in cidrs]
    findings = []
    for i, left in enumerate(ranges):
        for right in ranges[i + 1 :]:
            if left.contains(right):
                findings.append(
                    f"{left.cidr} contains {right.cidr}; the "
                    "narrower rule is dead unless it sorts "
                    "first"
                )
            elif right.contains(left):
                findings.append(
                    f"{right.cidr} contains {left.cidr}; the "
                    "narrower rule is dead unless it sorts "
                    "first"
                )
            elif left.overlaps(right):
                findings.append(
                    f"{left.cidr} and {right.cidr} partially "
                    "overlap; the effective policy depends on "
                    "evaluation order"
                )
    if not findings:
        return "no overlaps; each address matches one rule"
    return "\n".join(
        [f"{len(findings)} overlap(s):"]
        + [f"  {line}" for line in findings]
    )
