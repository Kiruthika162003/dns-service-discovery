"""The ring's promise, measured against the modulo baseline it replaced.

Two hundred keys, three members, a fourth joins: the drill
runs both worlds through the same key set and keeps the pair
of numbers that ends the architecture debate. Modulo
reassignment moves 153 of 200 keys, three quarters of
everything, because changing the divisor changes nearly every
remainder; the ring moves 40, exactly the arc the newcomer
takes, and every key outside that arc is verified untouched
by name. The second measured truth is the vnode lottery: one
point per member spreads 200 keys 119 against 14, a six-to-one
imbalance from pure hash luck, while sixty-four points per
member land 80 against 59. Both numbers are recomputed live
on every run because they are the kind of claim that drifts
into folklore the moment nobody remeasures it.
"""

from __future__ import annotations

import hashlib

from beacon.drills.finding import Finding
from beacon.hashring import HashRing, movement_on_change

KEYS = [f"key-{number}" for number in range(200)]


def _mod_owner(key: str, count: int) -> int:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:8], 16) % count


def run() -> Finding:
    ring = HashRing(vnodes=64)
    for member in ("alpha", "bravo", "charlie"):
        ring.join(member)
    before = ring.ownership_map(KEYS)
    ring.join("delta")
    after = ring.ownership_map(KEYS)
    ring_moved, _ = movement_on_change(before, after)
    untouched_verified = all(
        after[key] == before[key]
        for key in KEYS
        if after[key] != "delta"
    )
    mod_moved = sum(
        1
        for key in KEYS
        if _mod_owner(key, 3) != _mod_owner(key, 4)
    )
    lottery = HashRing(vnodes=1)
    for member in ("alpha", "bravo", "charlie"):
        lottery.join(member)
    lottery_report = lottery.spread_report(KEYS)
    balanced_report = HashRing(vnodes=64)
    for member in ("alpha", "bravo", "charlie"):
        balanced_report.join(member)
    spread = balanced_report.spread_report(KEYS)
    numbers = {
        "keys": 200,
        "ring_moved": ring_moved,
        "modulo_moved": mod_moved,
        "untouched_verified": untouched_verified,
        "lottery_imbalance": "heaviest 119, lightest 14"
        in lottery_report,
        "balanced": "heaviest 80, lightest 59" in spread,
    }
    holds = (
        numbers["ring_moved"] == 40
        and numbers["modulo_moved"] == 153
        and numbers["untouched_verified"]
        and numbers["lottery_imbalance"]
        and numbers["balanced"]
    )
    return Finding(
        drill="ringmath",
        claim=(
            "the fourth member takes 40 keys where modulo "
            "reshuffles 153, every key outside the arc "
            "verified untouched, and the vnode lottery runs "
            "119 against 14 until sixty-four points average "
            "it to 80 against 59; remeasured live because "
            "folklore starts where remeasurement stops"
        ),
        numbers=numbers,
        holds=holds,
    )
