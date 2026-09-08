"""LSM compaction: leveled layout trades high write amplification for low read and space cost.

A log-structured merge tree flushes sorted tables and then must
compact them, merging overlapping tables so reads do not have to
consult an ever-growing pile, and how it compacts sets three
amplifications that pull against each other. Leveled compaction keeps
each level non-overlapping and roughly a fanout factor larger than
the one above, so a read checks at most one table per level and the
levels number only the logarithm of the data size, giving low read
amplification, and because a level holds no duplicate keys the wasted
space is bounded, giving low space amplification. The price is write
amplification: as data moves down the levels it is rewritten about
the fanout times per level, so a single logical write can cause many
physical ones, which wears flash and consumes write bandwidth. The
alternative, size-tiered compaction, flips the trade, cheap writes
but higher read and space cost, so the choice is a workload decision,
not a default. The module computes the amplifications from the level
count and fanout and the number of levels a dataset needs, so the
three-way trade is a set of numbers an operator sizes against the
workload rather than a folklore preference.
"""

from __future__ import annotations

from math import ceil, log

from beacon.errors import Invalid


def levels_needed(total_size: int, level0_size: int, fanout: int) -> int:
    if total_size < 1 or level0_size < 1:
        raise Invalid("sizes must be positive")
    if fanout < 2:
        raise Invalid(
            "a fanout below two never grows the levels, so the tree "
            "collapses to one level"
        )
    if total_size <= level0_size:
        return 1
    return ceil(log(total_size / level0_size, fanout)) + 1


def write_amplification(levels: int, fanout: int) -> int:
    if levels < 1 or fanout < 2:
        raise Invalid("need at least one level and a fanout of two")
    return levels * fanout


def read_amplification(levels: int) -> int:
    if levels < 1:
        raise Invalid("a tree has at least one level")
    return levels
