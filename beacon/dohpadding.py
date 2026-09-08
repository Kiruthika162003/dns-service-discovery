"""DNS over HTTPS padding: the query is encrypted, and its length still talks.

Encrypting DNS hides the names from the network, but a passive
observer who cannot read the query can still measure its
length, and answer sizes correlate with sites: a distinctive
response size is a fingerprint that survives encryption. Padding
is the countermeasure, rounding every message up to a block
size so many different queries share one length and the size
channel goes quiet. The tension this module measures is the
obvious one, larger blocks hide more but waste more bandwidth,
and it does the counting honestly: distinct observable lengths
before and after padding on a set of message sizes, against the
padding bytes spent to collapse them. The finding the drill
keeps is that padding to a single fixed size is the strongest
privacy and the worst efficiency, while block padding trades a
little leakage for a lot of saved bytes, so the choice is a
real dial and not a checkbox, and a deployment that pads to
save bytes while claiming privacy is measuring the wrong axis.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


def pad_to_block(size: int, block: int) -> int:
    if size < 1 or block < 1:
        raise Invalid("sizes and blocks are positive")
    return -(-size // block) * block


@dataclass
class PaddingAnalysis:
    message_sizes: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.message_sizes:
            raise Invalid("no messages to analyze")

    def observable_lengths(self, block: int) -> int:
        return len(
            {
                pad_to_block(size, block)
                for size in self.message_sizes
            }
        )

    def padding_bytes(self, block: int) -> int:
        return sum(
            pad_to_block(size, block) - size
            for size in self.message_sizes
        )

    def privacy_report(self, block: int) -> str:
        before = len(set(self.message_sizes))
        after = self.observable_lengths(block)
        spent = self.padding_bytes(block)
        return (
            f"block {block}: {before} distinct length(s) "
            f"collapse to {after}, spending {spent} padding "
            f"byte(s); fewer lengths is more privacy and more "
            "bytes, a dial not a checkbox"
        )

    def compare_blocks(self, blocks: list[int]) -> str:
        if not blocks:
            raise Invalid("no block sizes to compare")
        lines = ["block: observable lengths / padding bytes"]
        for block in sorted(blocks):
            lines.append(
                f"  {block}: {self.observable_lengths(block)} "
                f"length(s), {self.padding_bytes(block)} byte(s)"
            )
        lines.append(
            "padding to one size is strongest privacy and worst "
            "efficiency; a deployment padding to save bytes "
            "while claiming privacy measures the wrong axis"
        )
        return "\n".join(lines)
