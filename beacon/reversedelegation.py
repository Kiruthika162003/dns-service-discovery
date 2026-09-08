"""Classless reverse delegation: handing out a piece of a /24 that does not fall on an octet.

Reverse DNS, the in-addr.arpa tree that maps addresses back to
names, delegates naturally on octet boundaries, a whole /8, /16, or
/24, because each label of the reversed address is one octet. That
leaves no clean way to delegate a block smaller than a /24, say a
/27 of thirty-two addresses, to the customer who owns it, since the
customer does not own the whole third-octet zone the addresses live
in. RFC 2317 works around it with a level of indirection. The owner
of the /24 keeps the zone but, for each address in the delegated
range, installs a CNAME pointing the ordinary reverse name to a name
inside a specially crafted sub-zone that the customer is delegated
and controls, so a reverse lookup follows the CNAME into the
customer's zone and finds the PTR there. The cost is the extra
CNAME hop per address and a naming convention both sides must agree
on, and the benefit is that a sub-/24 block gets its own authority
without owning an octet. The module decides whether a prefix needs
the classless workaround and builds the CNAME target for an address
in a delegated range, so the indirection is generated rather than
hand-typed.
"""

from __future__ import annotations

from beacon.errors import Invalid


def needs_classless(prefix: int) -> bool:
    if not 0 <= prefix <= 32:
        raise Invalid(f"a prefix of {prefix} is outside 0 to 32")
    return prefix > 24


def cname_target(
    last_octet: int, range_label: str, third_octet_zone: str
) -> str:
    if not 0 <= last_octet <= 255:
        raise Invalid(
            f"{last_octet} is not a final octet in 0 to 255"
        )
    return f"{last_octet}.{range_label}.{third_octet_zone}"


def build_delegation(
    start: int, count: int, range_label: str, third_octet_zone: str
) -> dict[str, str]:
    if count < 1 or start < 0 or start + count > 256:
        raise Invalid(
            "the delegated range must be a non-empty set of final "
            "octets within 0 to 255"
        )
    delegation = {}
    for octet in range(start, start + count):
        owner = f"{octet}.{third_octet_zone}"
        delegation[owner] = cname_target(
            octet, range_label, third_octet_zone
        )
    return delegation
