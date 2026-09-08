from __future__ import annotations

import pytest

from beacon.backpressure import FlowControl
from beacon.errors import Invalid, Refused


class TestSending:
    def test_it_sends_while_it_has_credits(self):
        flow = FlowControl(initial_credits=2)
        flow.send()
        flow.send()
        assert not flow.can_send()

    def test_sending_without_credit_is_refused(self):
        flow = FlowControl(initial_credits=0)
        with pytest.raises(Refused) as caught:
            flow.send()
        assert "wait\nfor a grant" in caught.value.args[0] or (
            "wait for a grant" in str(caught.value)
        )


class TestGranting:
    def test_a_grant_replenishes_the_window(self):
        flow = FlowControl(initial_credits=1)
        flow.send()
        assert not flow.can_send()
        flow.grant(3)
        assert flow.can_send()
        flow.send()
        flow.send()
        flow.send()
        assert not flow.can_send()

    def test_a_negative_grant_is_refused(self):
        with pytest.raises(Invalid) as caught:
            FlowControl(2).grant(-1)
        assert "does not\nclaw back" in caught.value.args[0] or (
            "does not claw back" in str(caught.value)
        )


class TestConstruction:
    def test_a_negative_balance_is_refused(self):
        with pytest.raises(Invalid):
            FlowControl(-1)
