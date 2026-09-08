"""Finalizers: hold the tombstone open until cleanup runs, so deletion orphans nothing.

A registered service usually owns external state, a DNS record, a
load-balancer entry, a health check, and deleting the service
record without removing those leaves them orphaned, pointing at
something that no longer exists. A finalizer prevents the orphan by
making deletion two-phase. When a delete is requested the object is
not removed immediately; it is marked with a deletion timestamp but
kept alive as long as any finalizer remains on it, which signals
that some controller still has cleanup to perform. Each controller
does its cleanup, removing the external state it owns, and then
removes its own finalizer, and only when the last finalizer is gone
does the object actually disappear, its side effects already
unwound. The mechanism has a failure mode the module makes visible:
a finalizer whose controller is broken or gone never gets removed,
so the object is stuck deleting forever, which is why real systems
add an escape hatch to force-remove a stuck finalizer. The module
tracks the finalizer set and the deletion mark, reports whether the
object may finally be removed, and treats a still-present finalizer
as the deliberate hold it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finalizable:
    finalizers: set[str] = field(default_factory=set)
    deleting: bool = False

    def add_finalizer(self, name: str) -> None:
        self.finalizers.add(name)

    def mark_delete(self) -> None:
        self.deleting = True

    def remove_finalizer(self, name: str) -> None:
        self.finalizers.discard(name)

    def may_be_removed(self) -> bool:
        return self.deleting and not self.finalizers

    def stuck_deleting(self) -> bool:
        return self.deleting and bool(self.finalizers)
