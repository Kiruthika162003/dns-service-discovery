"""A bitset: a set of small integers packed into bits, with word-speed union and intersection.

A set drawn from a bounded universe of small integers, enabled
feature flags, a fixed pool of node ids, the columns touched by a
query, can be represented not as a collection of objects but as bits
in a single integer, one bit per possible member. Membership is a
bit test, adding is a bit set, and the set operations become bitwise
arithmetic over the whole word at once: union is a bitwise or,
intersection a bitwise and, difference an and-not, each computing the
result for the entire universe in one operation rather than iterating
element by element as a hash set must. Counting the members is a
population count of the set bits. For a dense set over a modest
universe this is dramatically faster and more compact than a hash
set, which is why bitsets underpin flag registers, column masks, and
membership in fixed pools. The honest limit is sparsity: a set with a
few members drawn from an enormous universe wastes a bit for every
absent one, where a hash set stores only what is present, so the
bitset wins on dense-over-bounded and loses on sparse-over-huge. The
module adds and tests members, computes union, intersection, and
difference by bitwise operations, and counts the members.
"""

from __future__ import annotations

from beacon.errors import Invalid


class BitSet:
    def __init__(self) -> None:
        self.bits = 0

    def add(self, member: int) -> None:
        if member < 0:
            raise Invalid("a bitset holds non-negative members only")
        self.bits |= 1 << member

    def contains(self, member: int) -> bool:
        if member < 0:
            return False
        return bool(self.bits >> member & 1)

    def count(self) -> int:
        return bin(self.bits).count("1")

    def _wrap(self, bits: int) -> BitSet:
        other = BitSet()
        other.bits = bits
        return other

    def union(self, other: BitSet) -> BitSet:
        return self._wrap(self.bits | other.bits)

    def intersection(self, other: BitSet) -> BitSet:
        return self._wrap(self.bits & other.bits)

    def difference(self, other: BitSet) -> BitSet:
        return self._wrap(self.bits & ~other.bits)

    def members(self) -> list[int]:
        result = []
        bits = self.bits
        index = 0
        while bits:
            if bits & 1:
                result.append(index)
            bits >>= 1
            index += 1
        return result
