"""Bandwidth-delay product: the data a pipe holds in flight, and the window it takes to fill it.

Throughput on a network path is limited not only by bandwidth but by
how much data the sender is allowed to have unacknowledged at once,
the window, and the two meet at the bandwidth-delay product. The BDP
is the bandwidth times the round-trip time, the amount of data that
fits in the pipe end to end, and to keep the pipe full the window
must be at least that large: a window smaller than the BDP means the
sender exhausts it and stalls waiting for acknowledgements before the
first bytes have even returned, so throughput falls below the link's
capacity no matter how fast the link is. This is why a fat long pipe,
high bandwidth and high latency together, is hard: its BDP can be
enormous, and it exceeds the sixty-four kilobytes the original
sixteen-bit TCP window field can express, which is exactly the
limitation window scaling was introduced to lift. The module computes
the BDP in bytes from a bandwidth and a round trip, decides whether a
given window can fill the pipe, and flags when the BDP exceeds the
base window field so scaling is required, refusing negative inputs
that describe no path.
"""

from __future__ import annotations

from beacon.errors import Invalid

_BASE_WINDOW_MAX = 65535


def bdp_bytes(bandwidth_bps: float, rtt_seconds: float) -> float:
    if bandwidth_bps < 0 or rtt_seconds < 0:
        raise Invalid("bandwidth and round trip are never negative")
    return bandwidth_bps * rtt_seconds / 8


def fills_pipe(window_bytes: float, bandwidth_bps: float, rtt_seconds: float) -> bool:
    return window_bytes >= bdp_bytes(bandwidth_bps, rtt_seconds)


def needs_window_scaling(bandwidth_bps: float, rtt_seconds: float) -> bool:
    return bdp_bytes(bandwidth_bps, rtt_seconds) > _BASE_WINDOW_MAX
