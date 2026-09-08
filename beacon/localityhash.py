"""Topology-aware hashing: prefer a same-zone backend, fall back across zones only when needed.

Consistent hashing spreads keys evenly across a fleet, but it is
blind to where the backends sit, so a key can hash to a backend in a
distant zone while a perfectly good backend sits in the caller's own
zone, paying cross-zone latency and egress cost for nothing.
Topology-aware hashing keeps the even spread and the minimal
movement of rendezvous scoring but tilts the score toward backends
in the caller's zone, so a key prefers a local backend and only
spills to a remote one when the local zone has none that fit or all
are unhealthy. The tilt is a bounded preference, not an absolute
rule: a strong enough local preference keeps nearly all traffic in
zone while still letting a key cross zones rather than fail when it
must, which is the availability the preference must not sacrifice for
locality. The module scores backends with a same-zone bonus,
chooses the highest, and reports the fraction of keys kept in the
caller's zone, so the locality won is measured against the fraction
that had to spill, and an operator can see the preference working
rather than assume it.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def _base_score(key: str, backend: str) -> float:
    digest = hashlib.blake2b(
        f"{backend}\x00{key}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big") / 2**64


def _score(
    key: str, backend: str, backend_zone: str, caller_zone: str, bonus: float
) -> float:
    score = _base_score(key, backend)
    if backend_zone == caller_zone:
        score += bonus
    return score


def choose(
    key: str,
    backends: dict[str, str],
    caller_zone: str,
    bonus: float = 1.0,
) -> str:
    if not backends:
        raise Invalid("no backends to place the key on")
    if bonus < 0:
        raise Invalid(
            "a negative same-zone bonus would push traffic away "
            "from the local zone, the opposite of the intent"
        )
    return max(
        backends,
        key=lambda b: _score(key, b, backends[b], caller_zone, bonus),
    )


def local_fraction(
    keys: list[str],
    backends: dict[str, str],
    caller_zone: str,
    bonus: float = 1.0,
) -> float:
    if not keys:
        raise Invalid("no keys to measure locality over")
    local = sum(
        1
        for key in keys
        if backends[choose(key, backends, caller_zone, bonus)]
        == caller_zone
    )
    return local / len(keys)
