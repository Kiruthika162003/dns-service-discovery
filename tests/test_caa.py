from __future__ import annotations

from beacon.caa import may_issue


class TestPermissiveDefault:
    def test_no_records_lets_anyone_issue(self):
        assert may_issue([], "letsencrypt.org", wildcard=False)


class TestIssue:
    def test_a_listed_ca_may_issue(self):
        records = [("issue", "letsencrypt.org")]
        assert may_issue(records, "letsencrypt.org", wildcard=False)

    def test_an_unlisted_ca_may_not(self):
        records = [("issue", "letsencrypt.org")]
        assert not may_issue(records, "other-ca.com", wildcard=False)

    def test_the_empty_value_forbids_all_issuance(self):
        records = [("issue", ";")]
        assert not may_issue(records, "letsencrypt.org", wildcard=False)


class TestWildcard:
    def test_issuewild_governs_wildcards(self):
        records = [
            ("issue", "letsencrypt.org"),
            ("issuewild", "digicert.com"),
        ]
        assert may_issue(records, "digicert.com", wildcard=True)
        assert not may_issue(records, "letsencrypt.org", wildcard=True)

    def test_a_wildcard_falls_back_to_issue_without_issuewild(self):
        records = [("issue", "letsencrypt.org")]
        assert may_issue(records, "letsencrypt.org", wildcard=True)
