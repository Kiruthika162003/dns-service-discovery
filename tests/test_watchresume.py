from __future__ import annotations

import pytest

from beacon.errors import Invalid, Lagging
from beacon.watchresume import resume_plan


class TestResume:
    def test_a_version_inside_the_window_resumes(self):
        assert (
            resume_plan(
                client_version=50, oldest_retained=10, current_version=100
            )
            == "resume-incremental"
        )

    def test_the_oldest_retained_version_still_resumes(self):
        assert (
            resume_plan(10, oldest_retained=10, current_version=100)
            == "resume-incremental"
        )


class TestFallbacks:
    def test_a_version_off_the_window_must_resync(self):
        with pytest.raises(Lagging) as caught:
            resume_plan(5, oldest_retained=10, current_version=100)
        assert "full resync is required" in str(caught.value)

    def test_a_version_from_the_future_is_refused(self):
        with pytest.raises(Invalid):
            resume_plan(200, oldest_retained=10, current_version=100)
