"""A binary radix trie for longest-prefix match: the most specific rule wins.

Matching an address against a set of prefixes, an IP against routing
entries or an RPZ against CIDR blocks, is a longest-prefix problem:
several prefixes may contain the address and the most specific, the
longest, is the one that governs. A binary radix trie answers it in
time proportional to the address width rather than the number of
prefixes. Each prefix is stored by walking its bits from the most
significant, one trie level per bit, and marking the node at its
final bit with the prefix's value. A lookup walks the address's bits
down the same tree, remembering the deepest marked node it passed,
and that node is the longest matching prefix, because depth in the
trie is prefix length. The structure trades the memory of the tree
for a match cost that does not grow with the table, which is why
routers use it, and it naturally supports the most-specific-wins rule
without a separate sort. The module inserts a prefix given as an
address and a prefix length, looks up the longest matching prefix's
value for an address, and refuses a prefix length outside the address
width, since a prefix longer than the address is not a prefix of it.
"""

from __future__ import annotations

from beacon.errors import Invalid

_WIDTH = 32


def _to_int(addr: str) -> int:
    parts = addr.split(".")
    if len(parts) != 4:
        raise Invalid(f"{addr} is not a dotted IPv4 address")
    value = 0
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            raise Invalid(f"{part} is not an octet in {addr}")
        value = (value << 8) | int(part)
    return value


class RadixTree:
    def __init__(self) -> None:
        self.root: dict = {"value": None, "children": {}}

    def add(self, addr: str, length: int, value: str) -> None:
        if not 0 <= length <= _WIDTH:
            raise Invalid(
                f"a prefix length of {length} is outside 0 to "
                f"{_WIDTH}; it is not a prefix of the address"
            )
        bits = _to_int(addr)
        node = self.root
        for position in range(length):
            bit = (bits >> (_WIDTH - 1 - position)) & 1
            node = node["children"].setdefault(
                bit, {"value": None, "children": {}}
            )
        node["value"] = value

    def longest_match(self, addr: str) -> str | None:
        bits = _to_int(addr)
        node = self.root
        best = node["value"]
        for position in range(_WIDTH):
            bit = (bits >> (_WIDTH - 1 - position)) & 1
            if bit not in node["children"]:
                break
            node = node["children"][bit]
            if node["value"] is not None:
                best = node["value"]
        return best
