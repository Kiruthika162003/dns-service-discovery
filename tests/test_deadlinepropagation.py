from __future__ import annotations

import pytest

from beacon.deadlinepropagation import Deadline
from beacon.errors import Expired, Invalid


class TestConstruction:
    def test_a_nonpositive_budget_is_refused(self):
        with pytest.raises(Invalid):
            Deadline(0)


class TestMayStart:
    def test_work_that_fits_is_allowed(self):
        assert Deadline(200).may_start(50, 100)

    def test_work_that_does_not_fit_is_refused_fast(self):
        assert not Deadline(200).may_start(150, 100)

    def test_starting_past_the_deadline_raises(self):
        with pytest.raises(Expired) as caught:
            Deadline(200).may_start(200, 10)
        assert "nobody is waiting for" in str(caught.value)


class TestPropagation:
    def test_the_child_budget_subtracts_the_margin(self):
        assert Deadline(200).child_budget(50, 20) == 130

    def test_a_spent_budget_is_not_propagated(self):
        with pytest.raises(Expired) as caught:
            Deadline(200).child_budget(190, 20)
        assert "already spent is not worth propagating" in str(
            caught.value
        )


class TestWaste:
    def test_ignoring_the_deadline_names_the_wasted_work(self):
        assert Deadline(200).wasted_if_ignored(150, 200) == 200

    def test_fitting_work_wastes_nothing(self):
        assert Deadline(200).wasted_if_ignored(50, 100) == 0
