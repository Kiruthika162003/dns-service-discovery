"""Read preference: which replica answers a read, trading freshness against latency and load.

A replicated store gives a reader a choice of where to read, and the
choice is a real trade the application must make deliberately.
Reading from the primary is the freshest but concentrates load on one
node and pays its latency wherever it sits. Reading from a secondary
spreads load and can be nearer, but a secondary may lag, so the read
can be stale. Read preference names the policy. Primary insists on
the primary and fails if it is down. Primary-preferred uses the
primary when it is up and falls back to a secondary otherwise, trading
a little staleness for availability. Secondary insists on a secondary,
useful for offloading analytics that must not touch the primary.
Secondary-preferred uses a secondary when one is up and falls back to
the primary. Nearest ignores role and picks the lowest-latency healthy
replica, best for read-heavy latency-sensitive work that tolerates
staleness. The module selects a replica from a set given the
preference, honoring the fallbacks each mode allows and refusing when
a mode's requirement cannot be met, so the freshness-versus-latency
trade is an explicit policy rather than a hidden default.
"""

from __future__ import annotations

from beacon.errors import Refused

PREFERENCES = (
    "primary",
    "primary-preferred",
    "secondary",
    "secondary-preferred",
    "nearest",
)


def _healthy(replicas: list[dict], role: str) -> list[dict]:
    return [r for r in replicas if r["healthy"] and r["role"] == role]


def _nearest(candidates: list[dict]) -> dict:
    return min(candidates, key=lambda r: (r["latency"], r["id"]))


def select(preference: str, replicas: list[dict]) -> str:
    if preference not in PREFERENCES:
        raise Refused(
            f"{preference!r} is not a read preference; it knows "
            f"{', '.join(PREFERENCES)}"
        )
    primaries = _healthy(replicas, "primary")
    secondaries = _healthy(replicas, "secondary")
    if preference == "primary":
        pool = primaries
    elif preference == "secondary":
        pool = secondaries
    elif preference == "primary-preferred":
        pool = primaries or secondaries
    elif preference == "secondary-preferred":
        pool = secondaries or primaries
    else:
        pool = [r for r in replicas if r["healthy"]]
    if not pool:
        raise Refused(
            f"no healthy replica satisfies the {preference} "
            "preference; the read cannot be served under this policy"
        )
    return _nearest(pool)["id"]
