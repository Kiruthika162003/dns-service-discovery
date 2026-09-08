"""Query entropy: the poisoner must guess every bit you randomize.

An off-path attacker poisoning a cache must race the real
answer with a forgery that matches the question's transaction
id and port, and the defense budget is arithmetic: sixteen
bits of txid alone is 65536 possibilities, which a flood of
forgeries covers in seconds, and the birthday effect makes it
worse when many queries for the same name are in flight at
once, because the attacker's forgeries can match any of them.
Source port randomization multiplies the space by thousands,
and 0x20 case-flipping adds a bit per letter of the name, so
the guessing space for a twelve-letter name crosses thirty
bits and the race stops being winnable in an outage window.
The calculator prices attacks honestly: forgeries needed for
even odds against each defense stack, and the in-flight
multiplier that a resolver limiting duplicate questions takes
away, which is why query coalescing is a security feature
wearing an efficiency costume.
"""

from __future__ import annotations

from beacon.errors import Invalid

TXID_BITS = 16
PORT_BITS = 14


def _letters(name: str) -> int:
    return sum(1 for ch in name if ch.isalpha())


def guessing_space_bits(
    name: str,
    randomize_port: bool,
    case_flip: bool,
) -> int:
    bits = TXID_BITS
    if randomize_port:
        bits += PORT_BITS
    if case_flip:
        bits += _letters(name)
    return bits


def forgeries_for_even_odds(
    name: str,
    randomize_port: bool,
    case_flip: bool,
    in_flight: int = 1,
) -> int:
    if in_flight < 1:
        raise Invalid("at least one query must be in flight")
    space = 2 ** guessing_space_bits(
        name, randomize_port, case_flip
    )
    return space // (2 * in_flight)


def defense_table(name: str) -> str:
    stacks = (
        ("txid alone", False, False),
        ("txid + port", True, False),
        ("txid + port + 0x20", True, True),
    )
    lines = [f"forgeries for even odds against {name}:"]
    for label, port, flip in stacks:
        needed = forgeries_for_even_odds(name, port, flip)
        bits = guessing_space_bits(name, port, flip)
        lines.append(
            f"  {label}: {bits} bit(s), {needed} forgeries"
        )
    coalesced = forgeries_for_even_odds(
        name, True, True, in_flight=1
    )
    flooded = forgeries_for_even_odds(
        name, True, True, in_flight=200
    )
    lines.append(
        f"  200 in flight: {flooded} forgeries; coalescing "
        f"duplicates restores {coalesced}, which is why query "
        "coalescing is a security feature wearing an "
        "efficiency costume"
    )
    return "\n".join(lines)
