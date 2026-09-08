from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.leastconn import LeastConn


class TestRouting:
    def test_it_fills_the_least_loaded_backend(self):
        balancer = LeastConn(["a", "b", "c"])
        assert balancer.acquire() == "a"
        assert balancer.acquire() == "b"
        assert balancer.acquire() == "c"
        assert balancer.acquire() == "a"

    def test_a_pinned_backend_stops_receiving_work(self):
        balancer = LeastConn(["a", "b"])
        balancer.acquire()  # a -> 1
        balancer.acquire()  # b -> 1
        # a is stuck; do not release it, keep routing
        assert balancer.acquire() == "a"
        balancer.release("b")
        # now b has fewer; next goes to b
        assert balancer.acquire() == "b"

    def test_release_lowers_the_count(self):
        balancer = LeastConn(["a", "b"])
        balancer.acquire()
        balancer.release("a")
        assert balancer.load()["a"] == 0


class TestCap:
    def test_a_full_pool_refuses_to_route(self):
        balancer = LeastConn(["a", "b"], cap=1)
        balancer.acquire()
        balancer.acquire()
        with pytest.raises(Refused) as caught:
            balancer.acquire()
        assert "least-overloaded victim" in str(caught.value)


class TestRefusals:
    def test_no_backends_is_refused(self):
        with pytest.raises(Invalid):
            LeastConn([])

    def test_releasing_an_unknown_backend_is_refused(self):
        with pytest.raises(Invalid):
            LeastConn(["a"]).release("z")

    def test_a_double_release_is_refused(self):
        balancer = LeastConn(["a"])
        balancer.acquire()
        balancer.release("a")
        with pytest.raises(Invalid) as caught:
            balancer.release("a")
        assert "double release" in str(caught.value)
