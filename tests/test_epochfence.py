from __future__ import annotations

import pytest

from beacon.epochfence import EpochGuard
from beacon.errors import Fenced, Invalid


class TestAccept:
    def test_the_current_epoch_is_accepted(self):
        guard = EpochGuard()
        assert guard.accept(0) == "accepted"

    def test_advancing_moves_the_epoch(self):
        guard = EpochGuard()
        assert guard.advance() == 1
        assert guard.accept(1) == "accepted"


class TestFencing:
    def test_a_past_epoch_is_fenced(self):
        guard = EpochGuard()
        guard.advance()
        guard.advance()  # epoch 2
        with pytest.raises(Fenced) as caught:
            guard.accept(1)
        assert "superseded configuration" in str(caught.value)

    def test_a_whole_era_is_fenced_at_once(self):
        guard = EpochGuard()
        guard.advance()  # epoch 1
        # every operation from epoch 0 is fenced, not just one resource
        with pytest.raises(Fenced):
            guard.accept(0)


class TestFuture:
    def test_a_future_epoch_signals_a_missed_change(self):
        guard = EpochGuard()
        with pytest.raises(Invalid) as caught:
            guard.accept(5)
        assert "missed a configuration change" in str(caught.value)

    def test_a_negative_epoch_is_refused(self):
        with pytest.raises(Invalid):
            EpochGuard().accept(-1)
