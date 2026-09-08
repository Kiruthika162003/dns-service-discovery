"""EDNS TCP keepalive: reuse the connection across queries, but do not hoard idle sockets.

DNS over TCP, and over TLS above it, pays a real setup cost per
connection, a handshake and for TLS a key exchange, and a client
that opened a fresh connection for every query would pay that
cost on every lookup. RFC 7828 lets the server advertise how long
it will hold an idle connection open, so the client can send many
queries down one connection and amortize the handshake across all
of them. The advertised timeout is the whole trade in a single
number. Set it long and a busy client reuses the connection for
nearly free, but the server holds a socket for every client that
went quiet, and idle sockets are a finite resource an attacker can
exhaust by opening many and sending nothing. Set it short and the
reuse evaporates, every query racing the idle timer. The module
counts the handshakes a given timeout saves against a real stream
of inter-query gaps, so the operator sizes the timeout to the
traffic instead of to a guess.
"""

from __future__ import annotations

from beacon.errors import Invalid


def handshakes_without_keepalive(query_count: int) -> int:
    if query_count < 0:
        raise Invalid("a negative query count is not a workload")
    return query_count


def handshakes_with_keepalive(
    gaps_ms: list[int], idle_timeout_ms: int
) -> int:
    if idle_timeout_ms < 0:
        raise Invalid(
            "a negative idle timeout is not a duration; the "
            "connection is either held for some time or not at all"
        )
    handshakes = 1
    for gap in gaps_ms:
        if gap > idle_timeout_ms:
            handshakes += 1
    return handshakes


def handshakes_saved(
    gaps_ms: list[int], idle_timeout_ms: int
) -> int:
    query_count = len(gaps_ms) + 1
    return handshakes_without_keepalive(
        query_count
    ) - handshakes_with_keepalive(gaps_ms, idle_timeout_ms)


def idle_sockets_held(
    quiet_clients: int, idle_timeout_ms: int
) -> str:
    return (
        f"a {idle_timeout_ms}ms timeout holds up to "
        f"{quiet_clients} idle socket(s) for clients that went "
        "quiet; a long timeout buys reuse and pays it in sockets "
        "an attacker can exhaust by opening many and sending none"
    )
