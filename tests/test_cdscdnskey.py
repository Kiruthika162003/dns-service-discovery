from __future__ import annotations

import pytest

from beacon.cdscdnskey import CdsIntent, parent_apply
from beacon.errors import Invalid, Refused

CURRENT = {(111, 8, "aabb")}


class TestContinuity:
    def test_an_unsigned_cds_is_refused(self):
        with pytest.raises(Refused) as caught:
            parent_apply(
                CURRENT,
                [CdsIntent(222, 8, "ccdd")],
                signed_by_current_chain=False,
            )
        assert "trusts continuity" in str(caught.value)

    def test_a_signed_cds_replaces_the_ds(self):
        result = parent_apply(
            CURRENT,
            [CdsIntent(222, 8, "ccdd")],
            signed_by_current_chain=True,
        )
        assert result == {(222, 8, "ccdd")}

    def test_an_empty_cds_set_does_nothing(self):
        with pytest.raises(Invalid):
            parent_apply(CURRENT, [], signed_by_current_chain=True)


class TestDeleteSentinel:
    def test_algorithm_zero_takes_the_child_insecure(self):
        result = parent_apply(
            CURRENT,
            [CdsIntent(0, 0, "0")],
            signed_by_current_chain=True,
        )
        assert result == set()

    def test_deleting_when_already_insecure_is_refused(self):
        with pytest.raises(Invalid) as caught:
            parent_apply(
                set(),
                [CdsIntent(0, 0, "0")],
                signed_by_current_chain=True,
            )
        assert "already insecure" in str(caught.value)

    def test_mixing_delete_with_real_records_is_refused(self):
        with pytest.raises(Invalid) as caught:
            parent_apply(
                CURRENT,
                [CdsIntent(0, 0, "0"), CdsIntent(222, 8, "ccdd")],
                signed_by_current_chain=True,
            )
        assert "in the same breath" in str(caught.value)
