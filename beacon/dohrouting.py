"""Transport selection: plaintext, DoT, or DoH, each buying and costing something.

A resolver client picks a transport, and the choice is a
three-way trade nobody should make by default. Plaintext UDP
is fast and private to nobody: the network reads every name.
DNS over TLS encrypts on a dedicated port, private from the
network but obvious to it, since a firewall sees port 853 and
knows DNS is happening even if it cannot read what. DNS over
HTTPS hides inside ordinary web traffic on port 443, private
and unblockable by port, at the cost of the highest handshake
overhead and a dependency on a web stack. The selector scores
each on the axes that actually differ, network privacy,
blockability, and setup cost, and refuses to crown one, because
the right transport is a function of the threat model and a
client that picks DoH to defeat a passive eavesdropper paid
handshake cost against a threat DoT already stopped. The report
states which transport wins under a named threat, because
transport chosen without a threat model is cargo cult with
encryption.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

TRANSPORTS = ("plaintext", "dot", "doh")


@dataclass(frozen=True)
class TransportProfile:
    name: str
    network_can_read: bool
    network_can_block_by_port: bool
    handshake_cost: int

    def __post_init__(self) -> None:
        if self.name not in TRANSPORTS:
            raise Invalid(
                f"{self.name} is not a transport this client "
                f"speaks; it knows {', '.join(TRANSPORTS)}"
            )


PROFILES = {
    "plaintext": TransportProfile("plaintext", True, True, 0),
    "dot": TransportProfile("dot", False, True, 2),
    "doh": TransportProfile("doh", False, False, 5),
}


def recommend(threat: str) -> str:
    if threat == "passive-eavesdropper":
        return (
            "dot: encryption defeats a reader, and paying "
            "doh's handshake against a threat dot already "
            "stopped is cargo cult with encryption"
        )
    if threat == "port-blocking-firewall":
        return (
            "doh: only hiding in port 443 survives a firewall "
            "that blocks 853, and the handshake cost buys "
            "exactly that"
        )
    if threat == "none":
        return (
            "plaintext: with no threat, the encryption is "
            "overhead defending against nobody"
        )
    raise Invalid(
        f"unknown threat {threat!r}; transport chosen without "
        "a threat model is cargo cult with encryption"
    )


def comparison_table() -> str:
    lines = ["transport: reads / port-block / handshake"]
    for name in TRANSPORTS:
        profile = PROFILES[name]
        lines.append(
            f"  {name}: "
            f"{'readable' if profile.network_can_read else 'opaque'}"
            f", {'blockable' if profile.network_can_block_by_port else 'hidden'}"
            f", handshake {profile.handshake_cost}"
        )
    lines.append(
        "no transport wins outright; the right one is a "
        "function of the threat, not a default"
    )
    return "\n".join(lines)
