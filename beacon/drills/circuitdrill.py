"""The breaker's full arc, walked once: closed, open, half-open, and back.

A circuit breaker is a state machine, and a state machine is only
correct if every transition fires when it should, so the drill
walks the whole arc on one breaker rather than testing a state in
isolation. Two failures against a threshold of two open it; a
request during the cooldown is refused; after the cooldown a
single probe is admitted and a second is not; and the probe's
failure reopens the breaker at once. The drill holds the sequence
of allow decisions, refused then probed then refused again,
because a breaker that skipped the half-open gate and slammed
back to trusting a still-broken backend would pass a test that
only checked the open state and fail the users the half-open gate
exists to protect.
"""

from __future__ import annotations

from beacon.circuitbreaker import CircuitBreaker
from beacon.drills.finding import Finding


def run() -> Finding:
    breaker = CircuitBreaker(threshold=2, cooldown=10)
    breaker.on_failure(now=0)
    breaker.on_failure(now=1)
    open_blocks = not breaker.allow(now=5)
    probe_admitted = breaker.allow(now=11)
    second_blocked = not breaker.allow(now=12)
    breaker.on_failure(now=13)
    reopened = not breaker.allow(now=14)
    numbers = {
        "open_blocks_during_cooldown": open_blocks,
        "probe_admitted_after_cooldown": probe_admitted,
        "second_probe_blocked": second_blocked,
        "failed_probe_reopens": reopened,
    }
    holds = (
        open_blocks
        and probe_admitted
        and second_blocked
        and reopened
    )
    return Finding(
        drill="circuit",
        claim=(
            "the breaker opens on two failures, blocks during "
            "cooldown, admits exactly one probe after it, blocks "
            "a second, and reopens the instant the probe fails"
        ),
        numbers=numbers,
        holds=holds,
    )
