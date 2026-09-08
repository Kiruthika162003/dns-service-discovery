from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.svcbparams import client_must_ignore, validate_mandatory


class TestValidation:
    def test_a_valid_mandatory_list_passes(self):
        # keys present: alpn(1), port(3); mandatory names them
        assert validate_mandatory({1, 3}, [1, 3]) is None

    def test_mandatory_naming_itself_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_mandatory({0, 1}, [0])
        assert "require understanding of the requirement" in str(
            caught.value
        )

    def test_a_repeated_key_is_refused(self):
        with pytest.raises(Invalid):
            validate_mandatory({1}, [1, 1])

    def test_requiring_an_absent_key_is_refused(self):
        with pytest.raises(Invalid) as caught:
            validate_mandatory({1}, [3])
        assert "a contradiction" in str(caught.value)


class TestMustIgnore:
    def test_a_client_understanding_all_may_use_it(self):
        assert not client_must_ignore({1, 3}, {1, 3, 4})

    def test_a_client_missing_a_mandatory_key_must_ignore(self):
        assert client_must_ignore({1, 7}, {1, 3})
