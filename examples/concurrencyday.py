"""The concurrency day: an optimistic write loses a race, a deadlock is caught.

Run with: python -m examples.concurrencyday
"""

from __future__ import annotations

from beacon.deadlockdetection import find_cycle, has_deadlock
from beacon.mvcc import MVCC
from beacon.optimisticlock import OptimisticStore
from beacon.twophaselocking import compatible
from beacon.waitdie import wait_die


def morning_the_optimistic_race():
    store = OptimisticStore()
    _, a = store.read("k")
    _, b = store.read("k")
    store.commit("k", a, "from-a")
    try:
        store.commit("k", b, "from-b")
        outcome = "committed"
    except Exception:
        outcome = "aborted"
    print(f"morning  the race loser {outcome}; value stays {store.read('k')[0]}")


def midday_the_lock_compatibility():
    print(
        f"midday   shared+shared = {compatible('shared', 'shared')}, "
        f"shared+exclusive = {compatible('shared', 'exclusive')}"
    )


def afternoon_the_deadlock():
    wait_for = {"t1": {"t2"}, "t2": {"t3"}, "t3": {"t1"}}
    print(
        f"afternoon deadlock = {has_deadlock(wait_for)}, cycle "
        f"{sorted(find_cycle(wait_for))}"
    )


def evening_the_prevention():
    older = wait_die(requester_ts=1, holder_ts=5)
    younger = wait_die(requester_ts=5, holder_ts=1)
    print(f"evening  older requester -> {older}, younger requester -> {younger}")


def night_the_snapshot():
    store = MVCC()
    store.write("k", "v1", commit_ts=10)
    store.write("k", "v2", commit_ts=20)
    print(
        f"night    a snapshot at 15 reads {store.read('k', 15)} while a "
        f"later write to v2 does not block it"
    )


def main() -> int:
    morning_the_optimistic_race()
    midday_the_lock_compatibility()
    afternoon_the_deadlock()
    evening_the_prevention()
    night_the_snapshot()
    try:
        wait_die(3, 3)
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
