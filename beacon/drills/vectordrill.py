"""Version vectors catch the concurrent edit a scalar version silently drops.

The argument for version vectors over a single version number is
that a scalar cannot tell a strict descendant from a concurrent
edit, and the drill demonstrates exactly the update a scalar loses.
Two replicas both descend from the same state, then each makes an
independent edit; a scalar would compare the two version numbers,
keep the higher, and discard the other edit without a word. The
version vectors instead report the pair as concurrent, so the
conflict is surfaced rather than resolved by magnitude, and after a
merge the reconciled vector dominates both parents, proving the
merge remembered everything. The drill holds that the concurrent
pair is detected as concurrent, that a genuine descendant is
detected as dominating and not flagged, and that the merge settles
the conflict, which together are the capability a scalar version
does not have.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.versionvector import compare, is_conflict, merge


def run() -> Finding:
    base = {"a": 1, "b": 1}
    edit_a = {"a": 2, "b": 1}
    edit_b = {"a": 1, "b": 2}
    concurrent = compare(edit_a, edit_b)
    descendant = compare(edit_a, base)
    merged = merge(edit_a, edit_b)
    settled = not is_conflict(merged, edit_a) and not is_conflict(
        merged, edit_b
    )
    numbers = {
        "concurrent_verdict": concurrent,
        "descendant_verdict": descendant,
        "conflict_detected": concurrent == "concurrent",
        "merge_settles": settled,
    }
    holds = (
        concurrent == "concurrent"
        and descendant == "left-dominates"
        and settled
    )
    return Finding(
        drill="vectorclock",
        claim=(
            "two independent edits are reported concurrent where a "
            "scalar would drop one, a real descendant is reported "
            "dominating, and a merge settles the conflict so it "
            "cannot reappear"
        ),
        numbers=numbers,
        holds=holds,
    )
