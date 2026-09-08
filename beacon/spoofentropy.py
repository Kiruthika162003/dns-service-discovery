"""Spoofing entropy: the bits an off-path attacker must guess, and why one source is not enough.

An off-path attacker forging a DNS answer has to match the
query's identifying fields blind, racing the real answer from the
authority, and the whole defense is to make those fields hard to
guess. The transaction ID is sixteen bits, which alone is far too
few: the Kaminsky attack showed that by asking for many nonexistent
names an attacker gets unlimited fresh races and sixteen bits
falls in seconds. Source port randomization spreads the query
across the ephemeral range and adds roughly eleven bits, and 0x20
encoding, randomizing the case of each letter in the query name,
adds one more bit per letter at no protocol cost. The bits add
because the attacker must match every field in the same forged
packet, so the module sums the entropy from each source and turns
it into the expected number of forgery attempts to reach an even
chance, making the gulf concrete between a transaction ID standing
alone and the same ID with port and case randomization stacked
behind it.
"""

from __future__ import annotations

from beacon.errors import Invalid

TXID_BITS = 16


def entropy_bits(
    txid: bool = True,
    source_port_bits: int = 11,
    zero_x_twenty_letters: int = 0,
) -> int:
    if source_port_bits < 0 or zero_x_twenty_letters < 0:
        raise Invalid(
            "entropy is never negative; a field either adds bits "
            "of randomness or contributes none"
        )
    bits = TXID_BITS if txid else 0
    bits += source_port_bits
    bits += zero_x_twenty_letters
    if bits == 0:
        raise Invalid(
            "with no random field at all a forgery matches on the "
            "first try; there is no entropy to report"
        )
    return bits


def attempts_for_even_chance(bits: int) -> int:
    if bits < 1:
        raise Invalid(
            "fewer than one bit means the first guess is already "
            "even odds or better; there is nothing to count"
        )
    return 2 ** (bits - 1)


def compare(letters: int) -> str:
    alone = attempts_for_even_chance(entropy_bits(source_port_bits=0))
    stacked = attempts_for_even_chance(
        entropy_bits(zero_x_twenty_letters=letters)
    )
    return (
        f"txid alone: {alone} attempts to even odds; txid + port "
        f"+ {letters} letters of case: {stacked} attempts, the "
        "gulf that makes the same query practically unforgeable"
    )
