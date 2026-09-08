from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.soaserial import (
    date_serial,
    is_increase,
    revisions_exhausted,
    switch_would_freeze,
)


class TestDateSerial:
    def test_it_builds_the_date_and_revision(self):
        assert date_serial(2026, 9, 8, 3) == 2026090803

    def test_a_revision_past_99_is_refused(self):
        with pytest.raises(Invalid) as caught:
            date_serial(2026, 9, 8, 100)
        assert "99 edits in a day" in str(caught.value)

    def test_the_99th_revision_is_the_last(self):
        assert revisions_exhausted(99)
        assert not revisions_exhausted(50)


class TestIncrease:
    def test_a_larger_serial_is_an_increase(self):
        assert is_increase(2026090800, 2026090801)

    def test_an_equal_serial_is_not(self):
        assert not is_increase(100, 100)


class TestSwitchTrap:
    def test_switching_to_a_smaller_unixtime_would_freeze(self):
        # date-based 2026090800 vs a unix timestamp far smaller
        assert switch_would_freeze(2026090800, 1788900000)

    def test_a_genuine_increase_does_not_freeze(self):
        assert not switch_would_freeze(2026090800, 2026090801)
