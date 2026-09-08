"""A prefix trie: share common prefixes so autocomplete walks the prefix, not the dictionary.

Answering what words start with this prefix by scanning a list costs
the whole dictionary per query, and a trie removes that by sharing
structure. Each node is one character and each path from the root
spells a prefix, so all words sharing a prefix share the nodes up to
where they diverge, and finding every completion of a prefix means
walking to the node at the end of the prefix, once, and then
collecting the words in the subtree below it, work proportional to
the prefix length and the number of matches rather than the size of
the whole set. Membership and insertion are the same walk. The cost
the module keeps honest is memory: a node per character is generous
for a set of many short, unshared strings, where the pointers
outweigh the characters, which is why production tries compress runs
of single-child nodes into one, a radix or patricia trie, trading a
little lookup complexity for far fewer nodes. The module inserts a
word, tests membership, and lists all words with a given prefix in
sorted order, marking word ends so a prefix that is also a word is
found alongside its extensions.
"""

from __future__ import annotations


class Trie:
    def __init__(self) -> None:
        self.root: dict = {}
        self._end = "$"

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.setdefault(char, {})
        node[self._end] = True

    def contains(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node:
                return False
            node = node[char]
        return self._end in node

    def _node_for(self, prefix: str) -> dict | None:
        node = self.root
        for char in prefix:
            if char not in node:
                return None
            node = node[char]
        return node

    def with_prefix(self, prefix: str) -> list[str]:
        node = self._node_for(prefix)
        if node is None:
            return []
        found: list[str] = []

        def collect(current: dict, path: str) -> None:
            if self._end in current:
                found.append(path)
            for char in sorted(k for k in current if k != self._end):
                collect(current[char], path + char)

        collect(node, prefix)
        return found
