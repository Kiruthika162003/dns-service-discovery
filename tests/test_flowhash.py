from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.flowhash import flow_path, same_path

FLOW = ("10.0.0.1", "10.0.0.2", 5000, 443, "tcp")


class TestFlowPath:
    def test_the_same_flow_always_takes_the_same_path(self):
        assert flow_path(FLOW, 4) == flow_path(FLOW, 4)

    def test_the_path_is_in_range(self):
        assert 0 <= flow_path(FLOW, 8) < 8

    def test_a_reverse_direction_may_differ(self):
        # a different tuple can hash elsewhere; just assert it is valid
        reverse = ("10.0.0.2", "10.0.0.1", 443, 5000, "tcp")
        assert 0 <= flow_path(reverse, 8) < 8

    def test_zero_paths_is_refused(self):
        with pytest.raises(Invalid):
            flow_path(FLOW, 0)


class TestSamePath:
    def test_identical_flows_share_a_path(self):
        assert same_path(FLOW, FLOW, 4)

    def test_flows_spread_over_many_paths(self):
        flows = [
            ("10.0.0.1", "10.0.0.2", port, 443, "tcp") for port in range(200)
        ]
        paths = {flow_path(flow, 8) for flow in flows}
        assert len(paths) > 1
