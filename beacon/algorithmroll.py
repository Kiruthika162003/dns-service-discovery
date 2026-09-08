"""DNSSEC algorithm rollover: every published algorithm must sign everything, always.

Changing the algorithm a zone signs with is not a swap, it is a
careful overlap, because of a completeness rule that is easy to
violate and catastrophic when violated. RFC 4035 requires that
for every algorithm present in the zone's DNSKEY set there be
signatures over the zone made with that algorithm, since a
validator that understands only one algorithm must be able to
find both a key and a matching signature or it declares the zone
bogus. That rule dictates the order of a rollover and refutes the
tempting shortcut. One wants to publish the new DNSKEY first and
begin signing afterward, but publishing the key before its
signatures exist creates exactly the forbidden state, a DNSKEY
with no matching RRSIG, and every validator using the new
algorithm goes bogus. So the signatures come first: sign with the
new algorithm while still publishing only the old key, then
publish the new key, then withdraw the old key, and only last
withdraw the old signatures. The module validates that a proposed
state keeps completeness and refuses the shortcut by name.
"""

from __future__ import annotations

from beacon.errors import Invalid


def is_complete(
    published_algorithms: set[int], signing_algorithms: set[int]
) -> bool:
    missing = published_algorithms - signing_algorithms
    if missing:
        raise Invalid(
            f"algorithm(s) {sorted(missing)} have a published "
            "DNSKEY but no signatures; a validator that knows only "
            "one of them finds a key and no RRSIG and declares the "
            "zone bogus"
        )
    return True


def rollover_steps(old: int, new: int) -> list[str]:
    if old == new:
        raise Invalid(
            "the old and new algorithms are the same; there is no "
            "rollover to perform"
        )
    return [
        f"sign with {new} while publishing only key {old}",
        f"publish key {new} (now both {old} and {new} sign)",
        f"withdraw key {old} (only {new} signs and is published)",
        f"withdraw {old} signatures",
    ]


def validate_shortcut(publish_new_key_first: bool) -> None:
    if publish_new_key_first:
        raise Invalid(
            "publishing the new key before its signatures exist "
            "creates a DNSKEY with no matching RRSIG; sign first, "
            "then publish the key"
        )
