"""Suspicion timeout scales with the cluster, because a refutation needs time to cross it.

SWIM does not kill a member the instant it is suspected; it marks
it suspect, broadcasts that suspicion, and waits, because the
member or a witness may refute it with a fresher incarnation, and
the wait must be long enough for that refutation to travel. How
long depends on the cluster's size. Gossip spreads a fact in about
the logarithm of the member count in rounds, so the diameter a
refutation must cross grows with the log of the cluster, and a
suspicion timeout that was generous in a cluster of ten is
reckless in a cluster of ten thousand, declaring nodes dead before
the news that they are alive could possibly arrive. The timeout
therefore scales with the log of the cluster size times the probe
interval, wide enough that a true refutation almost always beats
it and no wider, so the dead are still reaped promptly. The module
computes that scaled timeout and refuses a cluster size below one,
since a cluster with no members has nobody to suspect and no
gossip to wait on.
"""

from __future__ import annotations

import math

from beacon.errors import Invalid


def suspicion_timeout(
    cluster_size: int,
    probe_interval: float,
    multiplier: float = 5.0,
) -> float:
    if cluster_size < 1:
        raise Invalid(
            "a cluster of fewer than one member has nobody to "
            "suspect and no gossip to wait on"
        )
    if probe_interval <= 0:
        raise Invalid(
            "the probe interval must be positive; the timeout is "
            "measured in probe intervals"
        )
    return multiplier * math.log10(cluster_size + 1) * probe_interval


def scales_with_cluster(
    small: int, large: int, probe_interval: float
) -> bool:
    return suspicion_timeout(large, probe_interval) > suspicion_timeout(
        small, probe_interval
    )
