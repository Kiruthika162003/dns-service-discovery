"""UDP payload negotiation: how big an answer may be before it must fall back to TCP.

DNS over UDP has a size ceiling, and the ceiling is negotiated, not
fixed. Without EDNS the limit is the ancient 512 bytes, small
enough that many real answers do not fit; with EDNS the client
advertises how large a UDP response it is willing to receive, and
the server sends up to the smaller of that and its own maximum. The
temptation is to advertise a very large buffer to avoid the fallback
to TCP, and it is a trap: a UDP datagram larger than the path can
carry in one packet gets fragmented, and IP fragments are both
unreliable, often dropped by middleboxes, and a spoofing aid, since
an attacker only needs to forge the first fragment. That is why the
post-flag-day recommendation settled at 1232 bytes, comfortably
under common path MTUs so a full answer arrives in one unfragmented
packet. When an answer will not fit the negotiated size the server
does not fragment or guess, it sets the truncated bit and lets the
client retry over TCP, which has no such limit. The module computes
the negotiated size with the 512 floor, and decides when an answer
must be truncated toward a TCP retry.
"""

from __future__ import annotations

from beacon.errors import Invalid

MINIMUM = 512
RECOMMENDED = 1232


def negotiated_size(
    client_advertised: int | None, server_max: int
) -> int:
    if server_max < MINIMUM:
        raise Invalid(
            f"a server maximum of {server_max} is below the 512 "
            "floor every DNS responder must support"
        )
    if client_advertised is None:
        return MINIMUM
    if client_advertised < 0:
        raise Invalid("an advertised buffer size is never negative")
    return max(MINIMUM, min(client_advertised, server_max))


def needs_truncation(response_size: int, negotiated: int) -> bool:
    return response_size > negotiated


def fragmentation_risk(advertised: int) -> bool:
    return advertised > RECOMMENDED
