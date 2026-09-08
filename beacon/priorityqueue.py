"""Priority with aging: serve the urgent first, but let the long-waiting rise past them.

Strict priority scheduling always serves the highest-priority item
available, which is exactly right until it is cruel: a steady stream
of high-priority work can keep a low-priority item waiting forever,
starved not because it was unimportant but because something more
important always arrived first. Aging is the fix that keeps strict
priority honest. An item's effective priority is its base priority
plus a term that grows with how long it has waited, so a low item
that has been waiting long enough eventually outranks a freshly
arrived high one and gets served, guaranteeing that every item is
served in bounded time no matter how much higher-priority work keeps
coming. The trade is a deliberate, bounded priority inversion: for
the aging to prevent starvation it must sometimes let a low item go
ahead of a high one, which is the point, not a bug, and the aging
rate tunes how long a low item may be made to wait before its turn
is forced. The module computes an item's effective priority from its
base and wait time and picks the next item as the one whose
effective priority is highest, breaking ties deterministically.
"""

from __future__ import annotations

from beacon.errors import Invalid


def effective_priority(base: int, waited: int, aging_rate: float) -> float:
    if aging_rate < 0:
        raise Invalid(
            "a negative aging rate would make waiting lower an "
            "item's priority, deepening starvation instead of "
            "curing it"
        )
    return base + waited * aging_rate


def next_item(
    items: list[tuple[str, int, int]], aging_rate: float
) -> str:
    if not items:
        raise Invalid("an empty queue has nothing to serve next")
    return max(
        items,
        key=lambda item: (
            effective_priority(item[1], item[2], aging_rate),
            item[0],
        ),
    )[0]
