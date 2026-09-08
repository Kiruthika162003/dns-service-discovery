from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.notifycooldown import NotifyDebouncer


class TestDebounce:
    def test_the_first_change_sends(self):
        assert NotifyDebouncer(cooldown=10).on_change(now=0) == "sent"

    def test_a_burst_coalesces(self):
        debouncer = NotifyDebouncer(cooldown=10)
        debouncer.on_change(now=0)
        assert debouncer.on_change(now=2) == "coalesced"
        assert debouncer.on_change(now=5) == "coalesced"

    def test_after_the_cooldown_it_sends_again(self):
        debouncer = NotifyDebouncer(cooldown=10)
        debouncer.on_change(now=0)
        debouncer.on_change(now=5)
        assert debouncer.on_change(now=10) == "sent"


class TestConstruction:
    def test_a_zero_cooldown_is_refused(self):
        with pytest.raises(Invalid):
            NotifyDebouncer(cooldown=0)
