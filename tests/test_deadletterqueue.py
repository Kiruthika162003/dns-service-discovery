from __future__ import annotations

import pytest

from beacon.deadletterqueue import DeliveryTracker
from beacon.errors import Invalid


class TestConstruction:
    def test_a_zero_maximum_is_refused(self):
        with pytest.raises(Invalid):
            DeliveryTracker(max_attempts=0)


class TestRetryThenDeadLetter:
    def test_it_retries_up_to_the_maximum(self):
        tracker = DeliveryTracker(max_attempts=3)
        assert tracker.attempt("poison") == "retry"
        assert tracker.attempt("poison") == "retry"
        assert tracker.attempt("poison") == "dead-letter"

    def test_a_dead_lettered_message_is_recorded(self):
        tracker = DeliveryTracker(max_attempts=2)
        tracker.attempt("poison")
        tracker.attempt("poison")
        assert tracker.is_dead_lettered("poison")

    def test_a_healthy_message_is_never_dead_lettered(self):
        tracker = DeliveryTracker(max_attempts=3)
        tracker.attempt("good")  # processed on first try in practice
        assert not tracker.is_dead_lettered("good")
        assert tracker.attempt_count("good") == 1


class TestIsolation:
    def test_messages_are_counted_independently(self):
        tracker = DeliveryTracker(max_attempts=2)
        tracker.attempt("a")
        tracker.attempt("b")
        assert tracker.attempt_count("a") == 1
        assert tracker.attempt_count("b") == 1
