from __future__ import annotations

from beacon.ownerrefs import collectible, orphans


class TestCollectible:
    def test_a_dependent_whose_owner_is_gone_is_collected(self):
        objects = {
            "endpoint-1": {"service-a"},
            "endpoint-2": {"service-a"},
        }
        # service-a has been deleted; it no longer exists
        assert collectible(objects, existing_owners=set()) == {
            "endpoint-1",
            "endpoint-2",
        }

    def test_a_dependent_with_a_surviving_owner_stays(self):
        objects = {"endpoint-1": {"service-a", "service-b"}}
        # service-b still exists, so the endpoint is not garbage
        assert collectible(objects, existing_owners={"service-b"}) == set()

    def test_an_object_with_no_owners_is_never_collected(self):
        objects = {"root-service": set()}
        assert collectible(objects, existing_owners=set()) == set()


class TestOrphans:
    def test_objects_missing_an_owner_ref_are_orphans(self):
        objects = {
            "owned": {"service-a"},
            "leaked": set(),
        }
        assert orphans(objects) == {"leaked"}

    def test_all_owned_objects_leave_no_orphans(self):
        objects = {"a": {"x"}, "b": {"y"}}
        assert orphans(objects) == set()
