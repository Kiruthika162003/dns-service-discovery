"""A skip list: a sorted structure that uses randomized express lanes to search in log time.

A skip list keeps elements in sorted order and searches, inserts, and
deletes them in expected logarithmic time, achieving with randomness
what a balanced tree achieves with careful rotations, and far more
simply. It is a stack of linked lists. The bottom list holds every
element in order, and each higher list is a sparser express lane
holding a random subset of the level below, so a search rides the top
express lane as far as it can without overshooting, then drops a level
and continues, skipping over long stretches of the bottom list the way
an express train skips local stops. The height of each element is
chosen by coin flips at insertion, so the lanes thin out geometrically
upward and the expected search cost is logarithmic without any
rebalancing, no rotations, no color invariants, just probabilities.
The trade against a balanced tree is that the bounds are expected, not
worst-case, a pathological run of coin flips could in principle build
a bad structure, though vanishingly unlikely, and the payment is the
extra forward pointers the express lanes cost. The module inserts a
key by finding its place at each level and splicing it in at a random
height, searches by descending the express lanes, and lists the keys
in sorted order along the bottom lane.
"""

from __future__ import annotations

import random

from beacon.errors import Invalid


class _Node:
    def __init__(self, key: int | None, height: int) -> None:
        self.key = key
        self.forward: list[_Node | None] = [None] * (height + 1)


class SkipList:
    def __init__(self, max_level: int = 16, probability: float = 0.5) -> None:
        if max_level < 1:
            raise Invalid("a skip list needs at least one level")
        if not 0.0 < probability < 1.0:
            raise Invalid("the promotion probability must be in (0, 1)")
        self.max_level = max_level
        self.probability = probability
        self.head = _Node(None, max_level)
        self.level = 0

    def _random_height(self) -> int:
        height = 0
        while random.random() < self.probability and height < self.max_level:
            height += 1
        return height

    def insert(self, key: int) -> None:
        update: list[_Node] = [self.head] * (self.max_level + 1)
        node = self.head
        for i in range(self.level, -1, -1):
            while node.forward[i] and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node
        successor = node.forward[0]
        if successor and successor.key == key:
            return
        height = self._random_height()
        if height > self.level:
            for i in range(self.level + 1, height + 1):
                update[i] = self.head
            self.level = height
        new = _Node(key, height)
        for i in range(height + 1):
            new.forward[i] = update[i].forward[i]
            update[i].forward[i] = new

    def contains(self, key: int) -> bool:
        node = self.head
        for i in range(self.level, -1, -1):
            while node.forward[i] and node.forward[i].key < key:
                node = node.forward[i]
        successor = node.forward[0]
        return successor is not None and successor.key == key

    def keys(self) -> list[int]:
        result: list[int] = []
        node = self.head.forward[0]
        while node:
            result.append(node.key)
            node = node.forward[0]
        return result
