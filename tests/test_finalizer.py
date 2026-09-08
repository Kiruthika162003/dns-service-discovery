from __future__ import annotations

from beacon.finalizer import Finalizable


class TestTwoPhaseDeletion:
    def test_an_object_with_finalizers_is_not_removed_on_delete(self):
        obj = Finalizable()
        obj.add_finalizer("dns-cleanup")
        obj.mark_delete()
        assert not obj.may_be_removed()

    def test_removing_the_last_finalizer_allows_removal(self):
        obj = Finalizable()
        obj.add_finalizer("dns-cleanup")
        obj.mark_delete()
        obj.remove_finalizer("dns-cleanup")
        assert obj.may_be_removed()

    def test_an_object_not_marked_for_deletion_stays(self):
        obj = Finalizable()
        obj.add_finalizer("dns-cleanup")
        assert not obj.may_be_removed()


class TestStuck:
    def test_a_lingering_finalizer_is_stuck_deleting(self):
        obj = Finalizable()
        obj.add_finalizer("broken")
        obj.mark_delete()
        assert obj.stuck_deleting()

    def test_a_clean_deletion_is_not_stuck(self):
        obj = Finalizable()
        obj.mark_delete()
        assert not obj.stuck_deleting()
        assert obj.may_be_removed()
