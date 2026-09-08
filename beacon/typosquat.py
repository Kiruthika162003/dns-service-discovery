"""Typo-squat detection: the name one keystroke from yours belongs to someone.

Attackers register domains a single edit away from a target,
gooogle and googel and goggle, catching the fraction of users
who mistype and harvesting whatever those users hand over.
Defenders watch for these registrations, and the core of the
watch is edit distance: a candidate within one edit of a
protected name is a squat suspect, and the module computes the
Levenshtein distance exactly rather than approximating,
because an off-by-one in the detector is a squat that slips or
a partner domain falsely accused. The homoglyph layer catches
what edit distance misses: characters that look identical but
are not, a Cyrillic letter standing in for a Latin one, which
is edit distance zero to the eye and one to the machine, so
the suspect list flags visual collisions separately with the
substituted character named. The verdict never auto-acts,
because taking down a domain is a legal act and a false
positive is a real business someone runs, so the detector
reports and the human decides.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

CONFUSABLES = {
    "a": chr(0x0430),
    "e": chr(0x0435),
    "o": chr(0x043E),
    "p": chr(0x0440),
    "c": chr(0x0441),
}


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, left_ch in enumerate(left, start=1):
        current = [i]
        for j, right_ch in enumerate(right, start=1):
            cost = 0 if left_ch == right_ch else 1
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


@dataclass
class SquatWatch:
    protected: str

    def __post_init__(self) -> None:
        if not self.protected:
            raise Invalid("an empty name protects nothing")

    def edit_suspect(self, candidate: str) -> str | None:
        distance = edit_distance(self.protected, candidate)
        if 1 <= distance <= 1:
            return (
                f"{candidate} is {distance} edit from "
                f"{self.protected}; a keystroke-away domain "
                "belongs to someone with a reason"
            )
        return None

    def homoglyph_suspect(self, candidate: str) -> str | None:
        for index, char in enumerate(self.protected):
            confusable = CONFUSABLES.get(char)
            if confusable is None:
                continue
            swapped = (
                self.protected[:index]
                + confusable
                + self.protected[index + 1 :]
            )
            if candidate == swapped:
                return (
                    f"{candidate} substitutes a lookalike for "
                    f"{char!r} at position {index}; edit "
                    "distance zero to the eye, one to the "
                    "machine"
                )
        return None

    def screen(self, candidates: list[str]) -> str:
        suspects = []
        for candidate in candidates:
            edit = self.edit_suspect(candidate)
            homoglyph = self.homoglyph_suspect(candidate)
            if homoglyph:
                suspects.append(f"HOMOGLYPH {homoglyph}")
            elif edit:
                suspects.append(f"TYPO {edit}")
        if not suspects:
            return (
                f"no suspects near {self.protected}; the "
                "neighborhood is clean this pass"
            )
        lines = [
            f"{len(suspects)} suspect(s) near {self.protected}; "
            "the detector reports and the human decides, "
            "because a takedown is a legal act and a false "
            "positive is a real business:"
        ]
        lines.extend(f"  {entry}" for entry in suspects)
        return "\n".join(lines)
