"""Causal broadcast: never deliver a message before the ones it causally depends on.

Broadcasting messages across replicas is not enough if the order
they arrive can invert cause and effect, because a reply delivered
before the message it replies to, or an update delivered before the
create it modifies, produces nonsense a receiver cannot repair.
Causal broadcast guarantees the order that matters: a message is
delivered at a replica only once every message that causally
precedes it has already been delivered there. Each message carries a
vector clock stamping what its sender had seen when it sent, and a
receiver holds a message back, buffered, until two conditions hold,
that the message is the very next one expected from its sender, one
past what the receiver has of that sender, and that the receiver has
already seen everything else the sender had seen. Only then is
delivering it safe, and delivering it may in turn unblock messages
that were waiting on it. The price is head-of-line latency: a single
delayed message stalls everything causally after it until it
arrives, which is the cost of never showing an effect before its
cause. The module decides deliverability from the local and message
vector clocks and applies a delivered message to advance the local
clock.
"""

from __future__ import annotations


def deliverable(
    local: dict[str, int], message: dict[str, int], sender: str
) -> bool:
    if message.get(sender, 0) != local.get(sender, 0) + 1:
        return False
    for node, seen in message.items():
        if node != sender and seen > local.get(node, 0):
            return False
    return True


def deliver(
    local: dict[str, int], message: dict[str, int], sender: str
) -> dict[str, int]:
    updated = dict(local)
    for node, seen in message.items():
        if node == sender:
            updated[node] = updated.get(node, 0) + 1
        else:
            updated[node] = max(updated.get(node, 0), seen)
    return updated
