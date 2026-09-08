"""Phi suspicion rises monotonically with silence and means the same at equal relative lateness.

The phi accrual detector's value over a hard timeout is that
suspicion is graded and scale-free, and the drill pins both. It
checks that phi climbs monotonically as the silence since the last
heartbeat lengthens, so a caller can pick any threshold and get a
consistent verdict, and it checks the scale-free property directly:
a link beating every second at three seconds of silence and a link
beating every ten at thirty seconds of silence produce the same
phi, so a threshold set once means the same thing on a fast link
and a slow one. A detector that rose non-monotonically, or whose
phi depended on the absolute interval rather than the relative
lateness, would force a per-link threshold and lose the whole
point, so the drill holds the monotonicity and the scale
invariance as the two properties that make one threshold enough.
"""

from __future__ import annotations

from itertools import pairwise

from beacon.drills.finding import Finding
from beacon.phi import PhiDetector


def run() -> Finding:
    fast = PhiDetector(1.0)
    samples = [fast.phi(t) for t in (1, 2, 4, 8, 16)]
    monotonic = all(
        later > earlier for earlier, later in pairwise(samples)
    )
    slow = PhiDetector(10.0)
    scale_free = abs(fast.phi(3) - slow.phi(30)) < 1e-9
    numbers = {
        "samples": [round(value, 3) for value in samples],
        "monotonic": monotonic,
        "fast_at_3": round(fast.phi(3), 4),
        "slow_at_30": round(slow.phi(30), 4),
        "scale_free": scale_free,
    }
    holds = monotonic and scale_free
    return Finding(
        drill="phi",
        claim=(
            "phi rises monotonically with silence and is scale "
            "free: a 1s link at 3s silence and a 10s link at 30s "
            "silence give the same phi, so one threshold serves "
            "every link"
        ),
        numbers=numbers,
        holds=holds,
    )
