from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.nsec3optout import OptOutSpan, savings_report


class TestDenial:
    def test_a_secure_name_is_always_provable_absent(self):
        assert OptOutSpan(opt_out=True).can_prove_absent("secure")
        assert OptOutSpan(opt_out=False).can_prove_absent("secure")

    def test_opt_out_cannot_deny_an_insecure_delegation(self):
        assert not OptOutSpan(opt_out=True).can_prove_absent(
            "insecure-delegation"
        )

    def test_without_opt_out_even_delegations_are_provable(self):
        assert OptOutSpan(opt_out=False).can_prove_absent(
            "insecure-delegation"
        )

    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(Invalid):
            OptOutSpan(opt_out=True).can_prove_absent("mystery")


class TestExplanation:
    def test_the_gap_names_the_trade(self):
        line = OptOutSpan(opt_out=True).explain(
            "insecure-delegation"
        )
        assert "may hide in the gap" in line


class TestSavings:
    def test_opt_out_leaves_the_delegations_unsigned(self):
        line = savings_report(1000, 40, opt_out=True)
        assert "40 secure names signed" in line
        assert "960 insecure delegations left unsigned" in line

    def test_no_opt_out_signs_everything(self):
        line = savings_report(1000, 40, opt_out=False)
        assert "all 1000 names" in line

    def test_more_secure_than_total_is_refused(self):
        with pytest.raises(Invalid):
            savings_report(10, 20, opt_out=True)
