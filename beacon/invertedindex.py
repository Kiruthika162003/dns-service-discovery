"""An inverted index: find records by term through set operations on short posting lists.

Finding every service tagged both production and database, or every
record mentioning a term, by scanning all records is linear in the
whole corpus and hopeless at scale. An inverted index turns the
question inside out. Instead of a record pointing to its terms, it
keeps, for each term, the set of records that contain it, its posting
list, so a query for a term is an immediate lookup of that list, and
a multi-term query becomes a set operation over a few lists: an AND
query intersects the posting lists so only records carrying every
term survive, and an OR query unions them so any matching record is
returned. The work is proportional to the sizes of the few posting
lists touched, not to the number of records, which is why it powers
both full-text search and tag-based service discovery. The cost is
the index's own memory and the discipline of updating it whenever a
record's terms change, since a stale posting list returns wrong
answers. The module adds a record under its terms, answers an AND
query by intersecting the posting lists and an OR query by unioning
them, treating a query term absent from the index as an empty list,
which correctly makes an AND with it return nothing.
"""

from __future__ import annotations


class InvertedIndex:
    def __init__(self) -> None:
        self.postings: dict[str, set[str]] = {}

    def add(self, doc_id: str, terms: set[str]) -> None:
        for term in terms:
            self.postings.setdefault(term, set()).add(doc_id)

    def query_and(self, terms: list[str]) -> set[str]:
        if not terms:
            return set()
        result = self.postings.get(terms[0], set()).copy()
        for term in terms[1:]:
            result &= self.postings.get(term, set())
        return result

    def query_or(self, terms: list[str]) -> set[str]:
        result: set[str] = set()
        for term in terms:
            result |= self.postings.get(term, set())
        return result
