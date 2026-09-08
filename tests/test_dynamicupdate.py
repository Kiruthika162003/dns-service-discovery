from __future__ import annotations

import pytest

from beacon.dynamicupdate import MutableZone, apply_update
from beacon.errors import Invalid


def zone() -> MutableZone:
    return MutableZone(
        {
            ("www.example.", "A"): {"192.0.2.1"},
            ("mail.example.", "A"): {"192.0.2.9"},
        }
    )


class TestPrerequisites:
    def test_a_missing_rrset_fails_with_nxrrset(self):
        with pytest.raises(Invalid) as caught:
            apply_update(
                zone(),
                [("rrset-exists", "ftp.example.", "A")],
                [],
            )
        assert "NXRRSET" in str(caught.value)

    def test_an_existing_name_fails_a_name_free_prereq(self):
        with pytest.raises(Invalid) as caught:
            apply_update(
                zone(),
                [("name-free", "www.example.", "A")],
                [("add", "www.example.", "A", "192.0.2.2")],
            )
        assert "YXDOMAIN" in str(caught.value)

    def test_a_present_rrset_fails_an_absent_prereq(self):
        with pytest.raises(Invalid) as caught:
            apply_update(
                zone(),
                [("rrset-absent", "www.example.", "A")],
                [],
            )
        assert "YXRRSET" in str(caught.value)


class TestAtomicApply:
    def test_a_satisfied_update_adds_the_record(self):
        after = apply_update(
            zone(),
            [("rrset-exists", "www.example.", "A")],
            [("add", "www.example.", "A", "192.0.2.2")],
        )
        assert after.rrsets[("www.example.", "A")] == {
            "192.0.2.1",
            "192.0.2.2",
        }

    def test_a_failed_prereq_writes_nothing(self):
        original = zone()
        with pytest.raises(Invalid):
            apply_update(
                original,
                [("rrset-exists", "ftp.example.", "A")],
                [("add", "www.example.", "A", "192.0.2.2")],
            )
        assert original.rrsets[("www.example.", "A")] == {
            "192.0.2.1"
        }

    def test_deleting_the_last_value_removes_the_rrset(self):
        after = apply_update(
            zone(),
            [],
            [("delete", "www.example.", "A", "192.0.2.1")],
        )
        assert not after.rrset_exists("www.example.", "A")

    def test_delete_rrset_removes_the_whole_set(self):
        after = apply_update(
            zone(),
            [],
            [("delete-rrset", "mail.example.", "A")],
        )
        assert not after.name_in_use("mail.example.")


class TestRefusals:
    def test_an_unknown_prerequisite_kind_is_refused(self):
        with pytest.raises(Invalid):
            apply_update(
                zone(), [("rrset-maybe", "www.example.", "A")], []
            )

    def test_an_unknown_update_op_is_refused(self):
        with pytest.raises(Invalid):
            apply_update(
                zone(), [], [("mutate", "www.example.", "A", "x")]
            )
