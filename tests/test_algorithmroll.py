from __future__ import annotations

import pytest

from beacon.algorithmroll import (
    is_complete,
    rollover_steps,
    validate_shortcut,
)
from beacon.errors import Invalid


class TestCompleteness:
    def test_a_fully_signed_set_is_complete(self):
        assert is_complete({8, 13}, {8, 13})

    def test_a_published_key_without_signatures_is_bogus(self):
        with pytest.raises(Invalid) as caught:
            is_complete({8, 13}, {8})
        assert "no RRSIG" in str(caught.value)

    def test_signing_with_more_than_published_is_still_complete(
        self,
    ):
        assert is_complete({8}, {8, 13})


class TestOrder:
    def test_the_steps_sign_before_publishing_the_new_key(self):
        steps = rollover_steps(8, 13)
        assert "sign with 13" in steps[0]
        assert "publish key 13" in steps[1]

    def test_a_no_op_rollover_is_refused(self):
        with pytest.raises(Invalid):
            rollover_steps(8, 8)


class TestShortcut:
    def test_publishing_the_new_key_first_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_shortcut(publish_new_key_first=True)
        assert "sign first" in str(caught.value)

    def test_the_correct_order_passes(self):
        assert validate_shortcut(publish_new_key_first=False) is None
