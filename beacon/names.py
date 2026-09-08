"""Domain names: case-blind, dot-rooted, and strict about their grammar.

DNS names look like strings and behave like paths read
backward, and half of resolution bugs come from treating them
as the former. The Name type normalizes at the door: lowercase,
trailing root dot required in the canonical form, labels
checked against the grammar, 63 bytes per label and 253 for
the whole name, hyphens forbidden at label edges. Comparison
is case-insensitive by construction rather than by discipline,
because WWW.Example.COM and www.example.com are the same name
in the protocol and any code path that forgets it mints a
cache that misses on capitalization. Ancestry is the other
half of the type's job: parent chains, subdomain tests, and
the wildcard rule as the RFC actually states it, a star
matches one or more leading labels but never the empty set,
so *.example.com covers a.example.com and a.b.example.com and
never example.com itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

MAX_LABEL = 63
MAX_NAME = 253
LABEL_OK = set("abcdefghijklmnopqrstuvwxyz0123456789-_")


@dataclass(frozen=True)
class Name:
    labels: tuple[str, ...]

    @classmethod
    def parse(cls, text: str) -> Name:
        if not text or text == ".":
            return cls(labels=())
        lowered = text.lower().rstrip(".")
        if not lowered:
            raise Invalid("a name needs at least one label")
        labels = lowered.split(".")
        total = sum(len(label) + 1 for label in labels)
        if total > MAX_NAME:
            raise Invalid(
                f"{len(lowered)} bytes exceeds the {MAX_NAME} "
                "byte ceiling the protocol grants a whole name"
            )
        for label in labels:
            cls._check_label(label)
        return cls(labels=tuple(labels))

    @staticmethod
    def _check_label(label: str) -> None:
        if not label:
            raise Invalid(
                "empty label: two dots in a row spell a name "
                "that cannot exist"
            )
        if len(label) > MAX_LABEL:
            raise Invalid(
                f"label {label[:12]}... is {len(label)} bytes "
                f"against the {MAX_LABEL} byte limit"
            )
        if label == "*":
            return
        stripped = set(label) - LABEL_OK
        if stripped:
            raise Invalid(
                f"label {label!r} carries "
                f"{''.join(sorted(stripped))!r}; this resolver "
                "speaks ascii and says so instead of guessing"
            )
        if label.startswith("-") or label.endswith("-"):
            raise Invalid(
                f"label {label!r} puts a hyphen at the edge"
            )

    def canonical(self) -> str:
        if not self.labels:
            return "."
        return ".".join(self.labels) + "."

    def is_root(self) -> bool:
        return not self.labels

    def parent(self) -> Name:
        if self.is_root():
            raise Invalid("the root has no parent")
        return Name(labels=self.labels[1:])

    def is_subdomain_of(self, other: Name) -> bool:
        if not other.labels:
            return True
        if len(self.labels) < len(other.labels):
            return False
        return (
            self.labels[-len(other.labels) :] == other.labels
        )

    def is_wildcard(self) -> bool:
        return bool(self.labels) and self.labels[0] == "*"

    def wildcard_matches(self, candidate: Name) -> bool:
        if not self.is_wildcard():
            raise Invalid(
                f"{self.canonical()} is not a wildcard"
            )
        stem = Name(labels=self.labels[1:])
        return (
            candidate.is_subdomain_of(stem)
            and len(candidate.labels) > len(stem.labels)
        )

    def ancestry(self) -> list[Name]:
        chain = []
        current = self
        while not current.is_root():
            chain.append(current)
            current = current.parent()
        chain.append(Name(labels=()))
        return chain
