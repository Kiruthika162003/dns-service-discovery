"""Every drill, one call, one page."""

from __future__ import annotations

import importlib

from beacon.drills.finding import Finding

DRILLS = (
    "beacon.drills.deadnames",
    "beacon.drills.ringmath",
)


def all_findings() -> list[Finding]:
    findings = []
    for dotted in DRILLS:
        module = importlib.import_module(dotted)
        findings.append(module.run())
    return findings


def broken() -> list[str]:
    return [
        finding.drill
        for finding in all_findings()
        if not finding.holds
    ]


def report() -> str:
    findings = all_findings()
    lines = [finding.line() for finding in findings]
    failing = sum(
        1 for finding in findings if not finding.holds
    )
    lines.append("")
    lines.append(f"{len(findings)} drills, {failing} broken")
    return "\n".join(lines)
