"""Aho-Corasick: match a whole set of patterns against text in one pass over the text.

Searching text for any of many patterns by running a single-pattern
search once per pattern costs the text length times the number of
patterns, which does not scale when the pattern set is large, a
blocklist of thousands of names, a filter of many keywords.
Aho-Corasick matches them all in one pass whose cost does not grow
with the number of patterns. It builds a trie of the patterns and
then adds failure links: from each trie node, a pointer to the node
representing the longest proper suffix of the string spelled to that
node that is also a prefix of some pattern, so that when a character
mismatches the search does not restart but follows the failure link
to the next-best partial match, exactly like the single-pattern
Knuth-Morris-Pratt automaton generalized to a set. The search then
reads the text once, following trie edges and failure links, and at
each node reports every pattern that ends there, caught by walking
the failure links so that a pattern which is a suffix of another is
not missed. The build costs the total length of the patterns and the
search the length of the text plus the matches. The module builds the
automaton from a set of patterns and returns every match as a pattern
and the position where it ends in the text.
"""

from __future__ import annotations

from collections import deque


class AhoCorasick:
    def __init__(self, patterns: list[str]) -> None:
        self.goto: list[dict[str, int]] = [{}]
        self.fail: list[int] = [0]
        self.output: list[list[str]] = [[]]
        for pattern in patterns:
            if pattern:
                self._add(pattern)
        self._build_failure_links()

    def _add(self, pattern: str) -> None:
        node = 0
        for char in pattern:
            if char not in self.goto[node]:
                self.goto.append({})
                self.fail.append(0)
                self.output.append([])
                self.goto[node][char] = len(self.goto) - 1
            node = self.goto[node][char]
        self.output[node].append(pattern)

    def _build_failure_links(self) -> None:
        queue: deque[int] = deque()
        for node in self.goto[0].values():
            self.fail[node] = 0
            queue.append(node)
        while queue:
            current = queue.popleft()
            for char, nxt in self.goto[current].items():
                queue.append(nxt)
                fallback = self.fail[current]
                while fallback and char not in self.goto[fallback]:
                    fallback = self.fail[fallback]
                self.fail[nxt] = self.goto[fallback].get(char, 0)
                if self.fail[nxt] == nxt:
                    self.fail[nxt] = 0
                self.output[nxt].extend(self.output[self.fail[nxt]])

    def search(self, text: str) -> list[tuple[str, int]]:
        matches: list[tuple[str, int]] = []
        node = 0
        for index, char in enumerate(text):
            while node and char not in self.goto[node]:
                node = self.fail[node]
            node = self.goto[node].get(char, 0)
            for pattern in self.output[node]:
                matches.append((pattern, index))
        return matches
