from __future__ import annotations

import pytest

from beacon.catalogsync import FederatedCatalog
from beacon.errors import Invalid


def catalog() -> FederatedCatalog:
    built = FederatedCatalog(cluster="west")
    built.register_local("billing")
    built.register_local("search")
    built.import_from("east", ["billing", "analytics"])
    return built


class TestImporting:
    def test_the_import_is_namespaced_by_origin(self):
        chosen = catalog()
        assert "east/billing" in chosen.imported
        assert chosen.imported["east/billing"] == "billing"

    def test_namespacing_prevents_the_collision(self):
        chosen = FederatedCatalog(cluster="west")
        chosen.register_local("billing")
        verdict = chosen.import_from("east", ["billing"])
        assert "prevented 1 collision(s)" in verdict

    def test_a_cluster_does_not_import_from_itself(self):
        with pytest.raises(Invalid) as caught:
            catalog().import_from("west", ["billing"])
        assert "with extra steps" in str(caught.value)


class TestResolution:
    def test_a_local_lookup_stays_local(self):
        assert catalog().resolve("billing") == "billing: local"

    def test_a_bare_name_never_reaches_a_remote_namesake(self):
        chosen = catalog()
        verdict_local = chosen.resolve("billing")
        assert "local" in verdict_local
        assert "imported" in chosen.resolve("east/billing")

    def test_an_unqualified_missing_name_is_refused(self):
        with pytest.raises(Invalid) as caught:
            catalog().resolve("unknown")
        assert "asked for by its cluster/name" in str(
            caught.value
        )


class TestTheBorder:
    def test_imported_services_never_re_export(self):
        chosen = catalog()
        with pytest.raises(Invalid) as caught:
            chosen.re_export_check("east/billing")
        assert "loops a registration around forever" in str(
            caught.value
        )

    def test_local_services_are_exportable(self):
        assert "exportable" in catalog().re_export_check(
            "search"
        )

    def test_the_border_report_separates_the_two(self):
        report = catalog().border_report()
        assert (
            "2 local service(s), 2 imported read-only"
        ) in report
        assert "one cluster's deploy is not another's outage" in (
            report
        )
