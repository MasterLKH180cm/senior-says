#!/usr/bin/env python3
"""Evaluate the reference routing policy or score recorded provider responses."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts.policy import DECISIONS, route_scenario
    from scripts.validate import validate_skill_tree
except ModuleNotFoundError:  # Direct execution from scripts/.
    from policy import DECISIONS, route_scenario
    from validate import validate_skill_tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "evaluation" / "scenarios.json"
DEFAULT_SKILL_ROOT = ROOT / "skills" / "engineering-agent-hierarchy"


@dataclass(frozen=True)
class CaseResult:
    """Expected and actual routing outcome for one scenario."""

    scenario_id: str
    passed: bool
    expected: Mapping[str, Any]
    actual: Mapping[str, Any]
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "expected": dict(self.expected),
            "actual": dict(self.actual),
            "error": self.error,
        }


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    """Load and schema-check a non-empty routing scenario corpus."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("scenario file must contain a non-empty JSON array")

    seen: set[str] = set()
    scenarios: list[dict[str, Any]] = []
    for index, raw in enumerate(data, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"scenario #{index} must be an object")

        scenario = dict(raw)
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError(f"scenario #{index} is missing a non-empty id")
        if scenario_id in seen:
            raise ValueError(f"duplicate scenario id: {scenario_id}")
        seen.add(scenario_id)

        title = scenario.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"scenario {scenario_id} is missing a non-empty title")

        expected = scenario.get("expected")
        if not isinstance(expected, dict):
            raise ValueError(f"scenario {scenario_id} is missing expected output")
        if expected.get("decision") not in DECISIONS:
            raise ValueError(f"scenario {scenario_id} has an invalid expected decision")
        if not isinstance(expected.get("must_escalate"), bool):
            raise ValueError(
                f"scenario {scenario_id} must define boolean expected.must_escalate"
            )

        # This validates all routing dimensions, triggers, and ambiguity fields.
        route_scenario(scenario)
        scenarios.append(scenario)

    return scenarios


def validate_skill_root(skill_root: Path) -> list[str]:
    """Compatibility wrapper around the canonical installed-skill validator."""

    return validate_skill_tree(Path(skill_root))


def evaluate_reference(scenarios: Iterable[Mapping[str, Any]]) -> list[CaseResult]:
    """Score the deterministic policy against expected corpus outcomes."""

    results: list[CaseResult] = []
    for scenario in scenarios:
        scenario_id = str(scenario["id"])
        expected = scenario["expected"]
        try:
            routed = route_scenario(scenario)
            actual = routed.as_dict()
            passed = (
                actual["decision"] == expected["decision"]
                and actual["must_escalate"] == expected["must_escalate"]
            )
            results.append(CaseResult(scenario_id, passed, expected, actual))
        except (KeyError, TypeError, ValueError) as exc:
            # Keep evaluating so one malformed case does not hide later failures.
            results.append(CaseResult(scenario_id, False, expected, {}, str(exc)))
    return results


def load_provider_responses(path: Path) -> dict[str, dict[str, Any]]:
    """Load provider output in array or {responses: [...]} form."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("responses"), list):
        items = data["responses"]
    else:
        raise ValueError(
            'provider responses must be an array or {"responses": [...]} object'
        )

    responses: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"provider response #{index} must be an object")
        scenario_id = item.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError(f"provider response #{index} needs scenario_id")
        if scenario_id in responses:
            raise ValueError(f"duplicate provider response: {scenario_id}")
        decision = item.get("decision")
        if decision not in DECISIONS:
            raise ValueError(
                f"provider response {scenario_id} has invalid decision: {decision}"
            )
        if not isinstance(item.get("must_escalate"), bool):
            raise ValueError(
                f"provider response {scenario_id} needs boolean must_escalate"
            )
        responses[scenario_id] = dict(item)
    return responses


def score_provider(
    scenarios: Iterable[Mapping[str, Any]],
    responses: Mapping[str, Mapping[str, Any]],
) -> list[CaseResult]:
    """Score provider responses and reject responses for unknown scenarios."""

    scenario_list = list(scenarios)
    known_ids = {str(scenario["id"]) for scenario in scenario_list}
    unknown_ids = set(responses) - known_ids
    if unknown_ids:
        raise ValueError(
            "provider responses contain unknown scenario id(s): "
            + ", ".join(sorted(unknown_ids))
        )

    results: list[CaseResult] = []
    for scenario in scenario_list:
        scenario_id = str(scenario["id"])
        expected = scenario["expected"]
        response = responses.get(scenario_id)
        if response is None:
            results.append(
                CaseResult(scenario_id, False, expected, {}, "missing response")
            )
            continue

        actual = {
            "decision": response["decision"],
            "must_escalate": response["must_escalate"],
        }
        expected_core = {
            "decision": expected["decision"],
            "must_escalate": expected["must_escalate"],
        }
        results.append(
            CaseResult(scenario_id, actual == expected_core, expected, actual)
        )
    return results


def build_report(
    mode: str,
    results: Sequence[CaseResult],
    skill_errors: Sequence[str],
) -> dict[str, Any]:
    passed = sum(result.passed for result in results)
    total = len(results)
    return {
        "mode": mode,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0.0,
            "skill_errors": list(skill_errors),
        },
        "cases": [result.as_dict() for result in results],
    }


def write_prompt_pack(path: Path, scenarios: Sequence[Mapping[str, Any]]) -> None:
    """Write provider-neutral prompts without embedding expected answers."""

    payload = {
        "instructions": (
            "For each scenario, apply the installed senior-says skill and return "
            "exactly scenario_id, decision, and must_escalate. Do not infer or add "
            "new scenarios."
        ),
        "allowed_decisions": sorted(DECISIONS),
        "scenarios": [
            {key: value for key, value in scenario.items() if key != "expected"}
            for scenario in scenarios
        ],
        "response_shape": {
            "provider": "<codex-or-claude>",
            "model": "<model>",
            "reasoning_effort": "<setting>",
            "skill_invocation": "<explicit-or-automatic>",
            "responses": [
                {
                    "scenario_id": "<id>",
                    "decision": "<allowed decision>",
                    "must_escalate": False,
                }
            ],
        },
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--skill-root", type=Path, default=DEFAULT_SKILL_ROOT)
    parser.add_argument(
        "--responses",
        type=Path,
        help="Score recorded Codex/Claude JSON output.",
    )
    parser.add_argument("--write-prompt-pack", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", type=Path, help="Write the full report to a file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scenarios = load_scenarios(args.scenarios)
        skill_errors = validate_skill_root(args.skill_root)
        if args.write_prompt_pack:
            write_prompt_pack(args.write_prompt_pack, scenarios)
        if args.responses:
            responses = load_provider_responses(args.responses)
            results = score_provider(scenarios, responses)
            mode = "provider"
        else:
            results = evaluate_reference(scenarios)
            mode = "reference-policy"
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = build_report(mode, results, skill_errors)
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2

    if args.format == "json":
        print(serialized)
    else:
        summary = report["summary"]
        print(
            f"{mode}: {summary['passed']}/{summary['total']} passed "
            f"({summary['pass_rate']:.1%})"
        )
        for error in skill_errors:
            print(f"SKILL ERROR: {error}")
        for result in results:
            if not result.passed:
                print(
                    f"FAIL {result.scenario_id}: expected={dict(result.expected)} "
                    f"actual={dict(result.actual)} error={result.error}"
                )

    return 0 if report["summary"]["failed"] == 0 and not skill_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
