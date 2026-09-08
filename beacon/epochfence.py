"""Epoch fencing: bump a number on each configuration change, reject anything from a past epoch.

A fencing token protects a single resource from a stale holder, but
a leadership or configuration change needs to fence a whole class of
operations at once, every write a superseded leader might still try,
not just those to one locked key. An epoch does that. It is a
monotonically increasing number bumped on each configuration change,
a new leader, a membership change, a reconfiguration, and every
operation carries the epoch it was issued under. A node applying
operations remembers the highest epoch it has seen and rejects any
operation stamped with an older one, so the instant the epoch
advances, every in-flight operation from the previous epoch is fenced
out together, wherever it was headed, without needing a per-resource
token. An operation stamped with a newer epoch than the node has seen
is also suspect, since it implies the node missed a configuration
change, and the module treats it as a signal to catch up rather than
blindly apply. The difference from a fencing token is scope: a token
fences one resource, an epoch fences an era. The module advances the
epoch, accepts an operation at the current epoch, and refuses one
from a past epoch as the stale actor it is.
"""

from __future__ import annotations

from beacon.errors import Fenced, Invalid


class EpochGuard:
    def __init__(self) -> None:
        self.current_epoch = 0

    def advance(self) -> int:
        self.current_epoch += 1
        return self.current_epoch

    def accept(self, operation_epoch: int) -> str:
        if operation_epoch < 0:
            raise Invalid("an epoch is never negative")
        if operation_epoch < self.current_epoch:
            raise Fenced(
                f"operation from epoch {operation_epoch} is fenced; "
                f"the current epoch is {self.current_epoch}, so it "
                "comes from a superseded configuration"
            )
        if operation_epoch > self.current_epoch:
            raise Invalid(
                f"operation from epoch {operation_epoch} is ahead of "
                f"the known {self.current_epoch}; the node missed a "
                "configuration change and must catch up first"
            )
        return "accepted"
