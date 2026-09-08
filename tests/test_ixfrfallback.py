from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ixfrfallback import bytes_saved, transfer_plan

JOURNAL = {100, 101, 102, 103}
CURRENT = 104


class TestPlan:
    def test_a_current_secondary_is_up_to_date(self):
        assert transfer_plan(104, JOURNAL, CURRENT) == "up-to-date"

    def test_a_serial_in_the_journal_takes_ixfr(self):
        assert transfer_plan(102, JOURNAL, CURRENT) == "ixfr"

    def test_a_serial_off_the_journal_falls_back_to_axfr(self):
        assert transfer_plan(50, JOURNAL, CURRENT) == "axfr"

    def test_a_secondary_ahead_of_the_primary_is_refused(self):
        with pytest.raises(Invalid) as caught:
            transfer_plan(200, JOURNAL, CURRENT)
        assert "cannot be newer than its source" in str(caught.value)


class TestSavings:
    def test_ixfr_saves_the_difference(self):
        assert bytes_saved(ixfr_size=200, axfr_size=5000, plan="ixfr") == 4800

    def test_axfr_saves_nothing(self):
        assert bytes_saved(200, 5000, plan="axfr") == 0
