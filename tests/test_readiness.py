from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.readiness import action, audit_liveness, routable


class TestActions:
    def test_a_dead_process_is_restarted(self):
        assert action(alive=False, ready=False) == "restart"

    def test_a_live_but_unready_instance_is_derouted(self):
        assert action(alive=True, ready=False) == "remove-from-lb"

    def test_a_live_ready_instance_serves(self):
        assert action(alive=True, ready=True) == "serve"

    def test_death_outranks_unreadiness(self):
        # dead and also unready still restarts, not deroutes
        assert action(alive=False, ready=True) == "restart"


class TestRoutable:
    def test_only_a_serving_instance_is_routable(self):
        assert routable(True, True)
        assert not routable(True, False)
        assert not routable(False, True)


class TestAudit:
    def test_a_shared_dependency_behind_liveness_is_refused(self):
        with pytest.raises(Invalid) as caught:
            audit_liveness(depends_on_shared_resource=True)
        assert "restarts the whole fleet" in str(caught.value)

    def test_a_self_only_liveness_is_safe(self):
        assert "safe from cascades" in audit_liveness(False)
