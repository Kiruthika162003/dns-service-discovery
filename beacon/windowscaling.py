"""TCP window scaling: multiply the 16-bit window by a power of two to fill a fat pipe.

The TCP header's window field is sixteen bits, so without help a
receiver can advertise at most sixty-four kilobytes of buffer, and
that ceiling throttles any path whose bandwidth-delay product is
larger, leaving the pipe half empty however fast the link. Window
scaling lifts the ceiling with a handshake option: each side declares
a shift count, and the advertised window is the sixteen-bit field
shifted left by that many bits, so a shift of seven multiplies the
window by a hundred twenty-eight and a shift of fourteen, the maximum,
by over sixteen thousand, enough for the largest realistic pipe. The
detail that makes it a commitment rather than a knob is that the
shift is negotiated once, at connection setup, and fixed for the life
of the connection, so it must be chosen for the path's bandwidth-delay
product up front. A shift set too small permanently caps the window
below what the pipe needs and cannot be raised later, quietly
limiting throughput for the whole connection. The module computes the
scaled window from the field and shift, the maximum window a shift
allows, and the smallest shift that covers a given bandwidth-delay
product, refusing a shift beyond the fourteen the option permits.
"""

from __future__ import annotations

from beacon.errors import Invalid

_MAX_SHIFT = 14
_FIELD_MAX = 65535


def scaled_window(window_field: int, shift: int) -> int:
    if not 0 <= window_field <= _FIELD_MAX:
        raise Invalid(f"the window field is 0..{_FIELD_MAX}")
    if not 0 <= shift <= _MAX_SHIFT:
        raise Invalid(
            f"a window scale shift is 0..{_MAX_SHIFT}; the option "
            "permits no more"
        )
    return window_field << shift


def max_window(shift: int) -> int:
    return scaled_window(_FIELD_MAX, shift)


def shift_for(bdp_bytes: int) -> int:
    if bdp_bytes < 0:
        raise Invalid("a bandwidth-delay product is never negative")
    for shift in range(_MAX_SHIFT + 1):
        if max_window(shift) >= bdp_bytes:
            return shift
    raise Invalid(
        f"a BDP of {bdp_bytes} exceeds even the maximum scaled window; "
        "no shift can cover it"
    )
