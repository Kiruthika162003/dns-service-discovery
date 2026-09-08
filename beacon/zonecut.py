"""The zone cut: which zone is actually authoritative for a name is its deepest enclosing apex.

Resolution walks down a tree of zones separated by cuts, points where
a parent delegates authority to a child, and deciding which zone
answers a name is not mere suffix matching but finding the deepest
cut that encloses it. Among all the zone apexes the resolver knows,
the one authoritative for a query is the longest that is the name
itself or an ancestor of it, the closest encloser, because a
delegation below a shallower apex has handed that part of the tree to
the deeper zone. Getting this wrong is a real bug, not a nicety: an
answer served from a parent zone for a name that lives below a
delegation returns data the parent no longer owns, stale or occluded
records the child would answer differently, so authority is decided
by the cut, not by whichever zone happens to match some suffix. The
module finds the zone cut for a name as the deepest enclosing apex,
decides whether one name encloses another, and reports when no known
apex encloses the name at all, which means the resolver holds no zone
authoritative for it and must refer or recurse rather than answer.
"""

from __future__ import annotations

from beacon.errors import Missing


def encloses(apex: str, name: str) -> bool:
    apex = apex.rstrip(".")
    name = name.rstrip(".")
    return name == apex or name.endswith("." + apex)


def zone_cut(qname: str, apexes: set[str]) -> str:
    enclosing = [apex for apex in apexes if encloses(apex, qname)]
    if not enclosing:
        raise Missing(
            f"no known zone encloses {qname}; the resolver holds "
            "nothing authoritative for it and must refer or recurse"
        )
    return max(enclosing, key=lambda apex: len(apex.rstrip(".")))
