"""Credit-based flow control: send only while holding credits the receiver granted.

A fast sender pointed at a slow receiver has to be stopped somewhere,
and doing it blindly, by dropping what overflows or by buffering
without bound, either loses data or moves the overload into memory
until it falls over. Credit-based flow control makes the receiver's
capacity explicit and binding. The receiver advertises credits, one
per slot of buffer it has free, and the sender may transmit only
while it holds credits, spending one per message and stopping dead at
zero. As the receiver drains its buffer it grants fresh credits back,
so the amount in flight is capped at exactly what the receiver said
it could hold and never more, and a slow receiver simply stops
granting until it catches up, which throttles the sender without a
drop or an unbounded queue. The cost is a round trip of latency at
the edge: when the sender spends its last credit it must wait for a
grant to arrive before sending again, so a sender that keeps its
window comfortably full hides the latency while one that runs the
credits to zero pays it. The module tracks the credit balance,
spends on send and refuses at zero, and grants credits back as the
receiver drains.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class FlowControl:
    def __init__(self, initial_credits: int) -> None:
        if initial_credits < 0:
            raise Invalid("a credit balance is never negative")
        self.credits = initial_credits

    def send(self) -> None:
        if self.credits <= 0:
            raise Refused(
                "no credits: the receiver's buffer is full and has "
                "granted nothing, so sending would overrun it; wait "
                "for a grant"
            )
        self.credits -= 1

    def grant(self, amount: int) -> None:
        if amount < 0:
            raise Invalid(
                "a negative grant would revoke credits already spent "
                "in flight; the receiver grants as it drains, it does "
                "not claw back"
            )
        self.credits += amount

    def can_send(self) -> bool:
        return self.credits > 0
