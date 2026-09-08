"""Metastable failure: how retries turn a brief spike into a self-sustaining overload.

The frightening failures in large systems are the ones that persist
after the thing that triggered them is gone, and retries are the
classic engine of that persistence. Consider a service running
comfortably under capacity when a brief spike pushes it over. The
requests that exceed capacity fail, and every failed request is
retried, so the failures generate extra load, and if the retry
multiplier is high enough that extra load alone keeps the service
over capacity even after the original spike has passed, the system
settles into a bad stable state, metastable failure, where retries
feed the overload that causes the retries, and it will not recover on
its own though the trigger is long gone. The module models exactly
that feedback. It computes the amplified load a level of offered
traffic produces once over-capacity requests retry, and it decides
whether a spike leaves behind a residual retry load that sustains the
overload after the spike, which is the metastable condition. The cure
it points at is the retry budget, capping retries so the feedback
cannot close the loop, tying this failure back to the mechanism built
to prevent it. The module computes the amplified load and detects the
sustained-overload condition, so the runaway is a decidable state.
"""

from __future__ import annotations

from beacon.errors import Invalid


def amplified_load(
    offered: float, capacity: float, retry_multiplier: float
) -> float:
    if capacity <= 0:
        raise Invalid("capacity must be positive")
    if retry_multiplier < 0:
        raise Invalid("a retry multiplier is never negative")
    failed = max(0.0, offered - capacity)
    return offered + failed * retry_multiplier


def residual_load(
    base: float, spike: float, capacity: float, retry_multiplier: float
) -> float:
    if capacity <= 0:
        raise Invalid("capacity must be positive")
    spike_failures = max(0.0, spike - capacity)
    return base + spike_failures * retry_multiplier


def is_metastable(
    base: float, spike: float, capacity: float, retry_multiplier: float
) -> bool:
    return (
        base <= capacity
        and residual_load(base, spike, capacity, retry_multiplier) > capacity
    )
