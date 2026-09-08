"""The election day: a leader is chosen, access is granted in turn, a stale era is fenced.

Run with: python -m examples.electionday
"""

from __future__ import annotations

from beacon.bullyelection import election_outcome, leader
from beacon.epochfence import EpochGuard
from beacon.lamportmutex import LamportMutex
from beacon.ricartagrawala import should_defer
from beacon.ringelection import leader as ring_leader


def morning_the_bully():
    print(
        f"morning  bully: no higher node -> {election_outcome(9, [])}, "
        f"leader of [2,7,4] is {leader([2, 7, 4])}"
    )


def midday_the_ring():
    print(f"midday   ring election of [3,7,1,5] elects {ring_leader([3, 7, 1, 5])}")


def afternoon_the_mutex():
    mutex = LamportMutex()
    mutex.request(2, "a")
    mutex.request(1, "b")
    head = mutex.head()
    print(
        f"afternoon mutex head is {head}, a with all acks may enter = "
        f"{mutex.may_enter('b', acks_received=1, total_nodes=2)}"
    )


def evening_the_defer():
    holder = should_defer("held", 0, "a", 5, "b")
    older = should_defer("wanted", 1, "a", 9, "b")
    print(f"evening  a holder defers = {holder}, an older wanter defers = {older}")


def night_the_epoch():
    guard = EpochGuard()
    guard.advance()  # epoch 1
    try:
        guard.accept(0)
        fenced = False
    except Exception:
        fenced = True
    print(f"night    an epoch-0 op after the bump is fenced = {fenced}")


def main() -> int:
    morning_the_bully()
    midday_the_ring()
    afternoon_the_mutex()
    evening_the_defer()
    night_the_epoch()
    try:
        ring_leader([3, 3, 5])
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
