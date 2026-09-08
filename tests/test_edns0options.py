from __future__ import annotations

import pytest

from beacon.edns0options import is_known, process
from beacon.errors import Invalid


class TestClassification:
    def test_known_options_are_recognized(self):
        assert is_known(10)  # COOKIE
        assert is_known(8)  # ECS

    def test_an_unknown_option_is_not_known(self):
        assert not is_known(4242)


class TestProcess:
    def test_known_options_are_handled_and_unknown_ignored(self):
        handled, ignored = process(
            [(10, b"cookie"), (4242, b"?"), (8, b"subnet")]
        )
        assert handled == ["COOKIE", "ECS"]
        assert ignored == [4242]

    def test_an_all_unknown_list_chokes_on_nothing(self):
        handled, ignored = process([(9990, b""), (9991, b"")])
        assert handled == []
        assert ignored == [9990, 9991]

    def test_a_negative_code_is_refused(self):
        with pytest.raises(Invalid) as caught:
            process([(-1, b"")])
        assert "not the impossible" in str(caught.value)
