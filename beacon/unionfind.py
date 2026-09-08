"""Union-find: track which nodes are in the same component as they merge, in near-constant time.

Membership systems and partition trackers keep asking the same
question, are these two nodes in the same connected group, as groups
merge over time, and answering it by recomputing connectivity from
scratch on every merge is wasteful. The disjoint-set, or union-find,
structure answers it incrementally. Each element points toward a
representative of its set, find follows those pointers to the root,
and union merges two sets by pointing one root at the other. Two
optimizations make it nearly free. Path compression flattens the
tree during find by pointing every node visited straight at the root,
so repeated queries get faster, and union by rank attaches the
shorter tree under the taller so the trees stay shallow. Together
they give an amortized cost per operation of the inverse Ackermann
function, which is less than five for any number of elements that
could physically exist, so find and union are effectively constant
time. That makes union-find the right tool for incremental
connectivity, merging gossip clusters, grouping equivalent records,
detecting when a partition heals into one component, without ever
rebuilding the whole relation. The module implements find with path
compression, union by rank, a connected query, and a count of the
distinct components remaining.
"""

from __future__ import annotations


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def _ensure(self, node: str) -> None:
        if node not in self.parent:
            self.parent[node] = node
            self.rank[node] = 0

    def find(self, node: str) -> str:
        self._ensure(node)
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != root:
            self.parent[node], node = root, self.parent[node]
        return root

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return
        if self.rank[root_a] < self.rank[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        if self.rank[root_a] == self.rank[root_b]:
            self.rank[root_a] += 1

    def connected(self, a: str, b: str) -> bool:
        return self.find(a) == self.find(b)

    def components(self) -> int:
        return len({self.find(node) for node in self.parent})
