"""Interval merging: collapse a messy set of ranges into the minimal disjoint set they cover.

Sets of ranges pile up in a system, address blocks in an ACL,
maintenance windows on a schedule, byte ranges of a file, and they
overlap and abut in ways that make membership and coverage questions
awkward to answer directly. Merging reduces them to a canonical form.
Sorting the intervals by start and then walking them once, extending
the current interval whenever the next one overlaps or touches it and
starting a fresh interval when it does not, yields the minimal set of
disjoint intervals that cover exactly the same points. Against that
merged form, deciding whether a point is covered is a simple search,
and the total covered length is a plain sum, both of which were
tangled when the intervals overlapped. Adjacent intervals that merely
touch, where one ends exactly where the next begins, are joined too,
since together they cover a contiguous span with no gap. The cost is
the initial sort, order n log n, paid once to make every later query
cheap. The module merges a set of intervals into the disjoint
minimal cover, decides whether a point falls in the cover, and sums
the total length, refusing an interval whose end precedes its start.
"""

from __future__ import annotations

from beacon.errors import Invalid


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    for lo, hi in intervals:
        if hi < lo:
            raise Invalid(
                f"interval ({lo}, {hi}) ends before it starts; that is "
                "not a range"
            )
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for lo, hi in ordered[1:]:
        last_lo, last_hi = merged[-1]
        if lo <= last_hi:
            merged[-1] = (last_lo, max(last_hi, hi))
        else:
            merged.append((lo, hi))
    return merged


def covers(merged: list[tuple[int, int]], point: int) -> bool:
    return any(lo <= point <= hi for lo, hi in merged)


def total_length(merged: list[tuple[int, int]]) -> int:
    return sum(hi - lo for lo, hi in merged)
