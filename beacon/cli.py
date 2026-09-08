"""The beacon command line: drills, check, summary, one page each."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="beacon")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "drills", help="run every drill and print the page"
    )
    sub.add_parser(
        "check", help="exit nonzero if any drill is broken"
    )
    sub.add_parser(
        "summary", help="one line: how many drills, how many broken"
    )
    args = parser.parse_args(argv)
    from beacon.drills import registry

    if args.command == "drills":
        print(registry.report())
        return 0
    if args.command == "check":
        failing = registry.broken()
        if failing:
            print(
                f"{len(failing)} drill(s) broken: "
                f"{', '.join(failing)}"
            )
            return 1
        print("all drills hold")
        return 0
    findings = registry.all_findings()
    failing_count = sum(
        1 for finding in findings if not finding.holds
    )
    print(f"{len(findings)} drills ({failing_count} broken)")
    return 1 if failing_count else 0


if __name__ == "__main__":
    sys.exit(main())
