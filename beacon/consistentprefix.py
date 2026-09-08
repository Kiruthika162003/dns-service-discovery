"""Consistent prefix: a reader may lag, but it always sees writes in order, never a gap.

Writes to a replicated store happen in an order, and the weakest
guarantee that still keeps a reader sane is that it sees some prefix
of that order: writes zero through k applied and nothing beyond,
never a later write without an earlier one. Without it a lagging
replica could show write five but not write three, which can be
nonsense, the reply present but not the question, the child record
present but not the parent it points to. Consistent prefix forbids
those gaps. A reader is allowed to be behind, seeing only an older
prefix, but whatever it sees is a genuine prefix of the write order,
internally coherent, so it never observes an effect before its
cause. This is weaker than linearizability, which would also require
the prefix to be the latest, and it is exactly enough to avoid the
impossible states, which is why replicated logs and change streams
offer it cheaply. The module checks whether a set of applied write
indices forms a contiguous prefix from the start, and points at the
gap when it does not, so the difference between a coherent lag and
an incoherent hole is decidable rather than assumed.
"""

from __future__ import annotations

from beacon.errors import Invalid


def is_prefix(applied: set[int]) -> bool:
    if not applied:
        return True
    return applied == set(range(max(applied) + 1))


def first_gap(applied: set[int]) -> int:
    if is_prefix(applied):
        raise Invalid(
            "the applied set is already a coherent prefix; there is "
            "no gap to point at"
        )
    for index in range(max(applied) + 1):
        if index not in applied:
            return index
    raise Invalid("unreachable: a non-prefix must have a gap")
