from __future__ import annotations

import pytest

from beacon.draindeadline import Drain
from beacon.errors import Refused


class TestPhases:
    def test_before_draining_it_serves(self):
        assert Drain(deadline=30).phase(now=0, inflight=5) == "serving"

    def test_draining_with_work_waits(self):
        drain = Drain(deadline=30)
        drain.begin()
        assert drain.phase(now=10, inflight=3) == "draining"

    def test_draining_with_no_work_is_done(self):
        drain = Drain(deadline=30)
        drain.begin()
        assert drain.phase(now=10, inflight=0) == "drained"

    def test_past_the_deadline_it_forces(self):
        drain = Drain(deadline=30)
        drain.begin()
        assert drain.phase(now=40, inflight=1) == "force"


class TestAccept:
    def test_a_serving_server_accepts(self):
        assert Drain(deadline=30).accept() is None

    def test_a_draining_server_refuses_new_work(self):
        drain = Drain(deadline=30)
        drain.begin()
        with pytest.raises(Refused) as caught:
            drain.accept()
        assert "belongs on a peer" in str(caught.value)
