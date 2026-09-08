from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lamportmutex import LamportMutex


class TestOrdering:
    def test_the_earliest_timestamp_heads_the_queue(self):
        mutex = LamportMutex()
        mutex.request(5, "b")
        mutex.request(2, "a")
        assert mutex.head() == (2, "a")

    def test_a_tie_breaks_by_node_id(self):
        mutex = LamportMutex()
        mutex.request(3, "b")
        mutex.request(3, "a")
        assert mutex.head() == (3, "a")

    def test_a_duplicate_request_is_refused(self):
        mutex = LamportMutex()
        mutex.request(1, "a")
        with pytest.raises(Invalid):
            mutex.request(1, "a")


class TestEntry:
    def test_the_head_with_all_acks_may_enter(self):
        mutex = LamportMutex()
        mutex.request(1, "a")
        mutex.request(2, "b")
        assert mutex.may_enter("a", acks_received=2, total_nodes=3)

    def test_the_head_without_all_acks_waits(self):
        mutex = LamportMutex()
        mutex.request(1, "a")
        assert not mutex.may_enter("a", acks_received=1, total_nodes=3)

    def test_a_non_head_may_not_enter(self):
        mutex = LamportMutex()
        mutex.request(1, "a")
        mutex.request(2, "b")
        assert not mutex.may_enter("b", acks_received=2, total_nodes=3)


class TestRelease:
    def test_release_lets_the_next_proceed(self):
        mutex = LamportMutex()
        mutex.request(1, "a")
        mutex.request(2, "b")
        mutex.release("a")
        assert mutex.head() == (2, "b")

    def test_releasing_a_missing_request_is_refused(self):
        with pytest.raises(Invalid):
            LamportMutex().release("ghost")
