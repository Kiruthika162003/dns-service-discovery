"""A BK-tree: index a dictionary for fuzzy lookup, pruning subtrees by the triangle inequality.

Edit distance tells how close two strings are, but finding every
dictionary word within a small distance of a query by measuring the
distance to each entry is linear in the dictionary, too slow at
scale. A BK-tree turns it sublinear by exploiting that edit distance
is a metric and so obeys the triangle inequality. The tree stores the
first word at the root and attaches every other word as a child
labeled by its distance to the node it hangs under, so distances
organize the structure. To search for all words within a radius of a
query, it computes the distance from the query to the current node,
reports the node if it is within the radius, and then descends only
into the children whose edge label lies within the radius of that
distance, because the triangle inequality guarantees no word reachable
through a child outside that band can be within the radius. Whole
subtrees are skipped without ever measuring their words, which is the
saving over a linear scan. The tree is built on top of a distance
function and is only as good as that metric's triangle inequality.
The module inserts words, searches for all within a radius using
Levenshtein distance, and prunes by the inequality, so the fuzzy
lookup an index alone cannot do is concrete.
"""

from __future__ import annotations

from beacon.errors import Invalid
from beacon.levenshtein import distance


class BKTree:
    def __init__(self) -> None:
        self.root: str | None = None
        self.children: dict[str, dict[int, str]] = {}

    def add(self, word: str) -> None:
        if self.root is None:
            self.root = word
            self.children[word] = {}
            return
        node = self.root
        while True:
            d = distance(word, node)
            if d == 0:
                return
            edges = self.children.setdefault(node, {})
            if d in edges:
                node = edges[d]
            else:
                edges[d] = word
                self.children[word] = {}
                return

    def search(self, query: str, radius: int) -> list[str]:
        if radius < 0:
            raise Invalid("a search radius is never negative")
        if self.root is None:
            return []
        found: list[str] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            d = distance(query, node)
            if d <= radius:
                found.append(node)
            for edge_distance, child in self.children.get(node, {}).items():
                if d - radius <= edge_distance <= d + radius:
                    stack.append(child)
        return sorted(found)
