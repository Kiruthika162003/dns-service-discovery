"""DNS name compression: pointers that must always point backward, or the resolver loops.

A DNS message repeats names constantly, the same zone suffix under
answer after answer, so the wire format lets a name end in a
pointer to an earlier occurrence instead of spelling it out again,
saving bytes on every response. The pointer is an offset into the
message, and the one rule that keeps decompression safe is that a
pointer must point strictly backward, to a name that has already
been written. A pointer to its own position, or forward to a name
not yet seen, or into a cycle of pointers, gives a decompressor no
base case: it follows the chain forever, and a crafted message of a
few bytes can hang or crash a parser that trusts the offsets. So a
decompressor must refuse any pointer that does not decrease the
offset and must track the offsets it has visited to catch a cycle
that individually-backward pointers could still form. The module
decompresses a name by following its labels and pointers, refuses a
non-backward pointer by name, and raises on a revisited offset,
treating the decompression loop as the denial-of-service vector it
is rather than an unusual input.
"""

from __future__ import annotations

from beacon.errors import Invalid, Loop


def decompress(entries: dict[int, tuple], start: int) -> list[str]:
    labels: list[str] = []
    visited: set[int] = set()
    offset = start
    while True:
        if offset in visited:
            raise Loop(
                f"compression pointer revisits offset {offset}; the "
                "chain forms a cycle with no base case and would "
                "loop forever"
            )
        visited.add(offset)
        if offset not in entries:
            raise Invalid(
                f"pointer targets offset {offset}, which holds no "
                "name; a dangling pointer decompresses to nothing"
            )
        entry = entries[offset]
        kind = entry[0]
        if kind == "pointer":
            target = entry[1]
            if target >= offset:
                raise Invalid(
                    f"pointer at {offset} targets {target}, not "
                    "strictly backward; a forward or self pointer is "
                    "the decompression-loop attack"
                )
            offset = target
        elif kind == "label":
            text, nxt = entry[1], entry[2]
            if text == "":
                return labels
            labels.append(text)
            offset = nxt
        else:
            raise Invalid(f"{kind!r} is not a wire entry kind")
