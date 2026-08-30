#!/usr/bin/env python3
"""Try one deterministic senior-says routing scenario locally."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts.evaluate import DEFAULT_SCENARIOS, load_scenarios
    from scripts.policy import route_scenario
except ModuleNotFoundError:  # Direct execution from scripts/.
    from evaluate import DEFAULT_SCENARIOS, load_scenarios
    from policy import route_scenario


def find_scenario(
    scenarios: Sequence[Mapping[str, Any]], scenario_id: str
) -> Mapping[str, Any] | None:
    return next((scenario for scenario in scenarios if scenario["id"] == scenario_id), None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", nargs="?", help="Scenario id to evaluate.")
    parser.add_argument("--list", action="store_true", help="List available scenarios.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scenarios = load_scenarios(args.scenarios)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for scenario in scenarios:
            print(f"{scenario['id']}: {scenario['title']}")
        return 0

    if not args.scenario:
        print("A scenario id is required unless --list is used.", file=sys.stderr)
        return 2

    selected = find_scenario(scenarios, args.scenario)
    if selected is None:
        print(f"Unknown scenario: {args.scenario}", file=sys.stderr)
        return 2

    decision = route_scenario(selected)
    expected = selected["expected"]
    print(f"Scenario: {selected['title']}")
    print(
        "Classification: "
        f"complexity={selected['implementation_complexity']}, "
        f"reasoning=R{selected['reasoning_depth']}, risk={selected['risk']}, "
        f"ambiguity={selected['ambiguity']}, "
        f"familiarity={selected['domain_familiarity']}"
    )
    print(f"Decision: {decision.decision}")
    print(f"Must escalate: {str(decision.must_escalate).lower()}")
    for reason in decision.rationale:
        print(f"Reason: {reason}")

    matches = (
        decision.decision == expected["decision"]
        and decision.must_escalate == expected["must_escalate"]
    )
    print(f"Expected decision: {expected['decision']}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
