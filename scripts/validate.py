#!/usr/bin/env python3
"""Validate the repository layout or one installed canonical skill tree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts.policy import DECISIONS, route_scenario
except ModuleNotFoundError:  # Direct execution from scripts/.
    from policy import DECISIONS, route_scenario

ROOT = Path(__file__).resolve().parents[1]
NAME = "engineering-agent-hierarchy"
SKILL_NAME = NAME
PLUGIN_NAME = "senior-says"
SEMVER_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
REFERENCE_FILES = (
    "reasoning-depth-and-routing.md",
    "delegation-and-escalation-protocol.md",
    "work-packet-template.md",
    "review-and-integration-protocol.md",
    "development-execution-contract.md",
)
CONTRACT_MARKERS = (
    "Development Execution Contract",
    "GitHub PR Review Inbox",
    "Mandatory code review",
    "Definition of Done",
)
SKILL_MARKERS = (
    "HIGH tier",
    "LOW tier",
    "REVIEW tier",
    "Implementation complexity",
    "reasoning depth",
    "risk",
    "ambiguity",
    "domain familiarity",
    "Escalation is mandatory",
    "BLOCKED_DECISION",
)
REPOSITORY_TOOLING = (
    Path("CONTRIBUTING.md"),
    Path(".github/pull_request_template.md"),
    Path(".github/workflows/ci.yml"),
    Path("scripts/__init__.py"),
    Path("scripts/install.py"),
    Path("scripts/validate.py"),
    Path("scripts/policy.py"),
    Path("scripts/evaluate.py"),
    Path("scripts/trial.py"),
    Path("scripts/benchmark.py"),
    Path("scripts/smoke_test.py"),
    Path("evaluation/README.md"),
    Path("evaluation/scenarios.json"),
    Path("tests/test_install.py"),
    Path("tests/test_policy.py"),
    Path("tests/test_evaluate.py"),
    Path("tests/test_validate.py"),
    Path("tests/test_trial.py"),
    Path("tests/test_benchmark.py"),
)


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse the simple scalar YAML frontmatter required by this repository."""

    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) != 3:
        return None

    values: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            return None
        values[key.strip()] = value.strip()
    return values


def validate_frontmatter(path: Path, root: Path) -> list[str]:
    if not path.is_file():
        return [f"missing: {display_path(path, root)}"]

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read {display_path(path, root)}: {exc}"]

    frontmatter = parse_frontmatter(text)
    if frontmatter is None:
        return [f"frontmatter missing or malformed: {display_path(path, root)}"]

    errors: list[str] = []
    if frontmatter.get("name") != NAME:
        errors.append(f"name mismatch: {display_path(path, root)}")
    if not frontmatter.get("description"):
        errors.append(f"description missing: {display_path(path, root)}")
    return errors


def validate_skill_tree(skill_root: Path) -> list[str]:
    """Validate an installed or canonical skill directory."""

    skill_root = Path(skill_root).expanduser()
    errors: list[str] = []
    if skill_root.is_symlink():
        errors.append(f"skill root must not be a symlink: {skill_root}")
    if skill_root.is_dir():
        for path in skill_root.rglob("*"):
            if path.is_symlink():
                errors.append(
                    f"skill tree contains symlink: {display_path(path, skill_root)}"
                )

    skill_file = skill_root / "SKILL.md"
    reference_root = skill_root / "references"

    errors.extend(validate_frontmatter(skill_file, skill_root))
    for filename in REFERENCE_FILES:
        path = reference_root / filename
        if not path.is_file():
            errors.append(f"missing: {display_path(path, skill_root)}")

    if skill_file.is_file():
        try:
            skill_text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read SKILL.md: {exc}")
        else:
            for marker in SKILL_MARKERS:
                if marker.casefold() not in skill_text.casefold():
                    errors.append(f"canonical skill missing marker: {marker}")
            for filename in REFERENCE_FILES:
                expected = f"references/{filename}"
                if expected not in skill_text:
                    errors.append(f"canonical skill does not reference: {expected}")

    contract = reference_root / "development-execution-contract.md"
    if contract.is_file():
        try:
            contract_text = contract.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read execution contract: {exc}")
        else:
            for marker in CONTRACT_MARKERS:
                if marker not in contract_text:
                    errors.append(f"execution contract missing marker: {marker}")

    return errors


def validate_codex_plugin(root: Path) -> list[str]:
    """Validate the skill-only Codex plugin manifest and referenced skill path."""

    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return ["missing tooling: .codex-plugin/plugin.json"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"invalid Codex plugin manifest: {exc}"]

    if not isinstance(manifest, dict):
        return ["Codex plugin manifest must be a JSON object"]

    errors: list[str] = []
    if manifest.get("name") != PLUGIN_NAME:
        errors.append(f"Codex plugin manifest name must be {PLUGIN_NAME}")
    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
        errors.append("Codex plugin manifest version must use semantic versioning")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("Codex plugin manifest description is missing")
    if manifest.get("skills") != "./skills/":
        errors.append("Codex plugin manifest skills must point to ./skills/")
    if not (root / "skills" / NAME / "SKILL.md").is_file():
        errors.append("Codex plugin manifest references a missing canonical skill")
    return errors


def _load_json_array(path: Path, label: str) -> tuple[list[Any], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [], [f"invalid {label}: {exc}"]
    if not isinstance(payload, list) or not payload:
        return [], [f"{label} must contain a non-empty JSON array"]
    return payload, []


def validate_evaluation_corpus(root: Path) -> list[str]:
    """Validate scenario schema, uniqueness, coverage, and expected routing."""

    path = root / "evaluation" / "scenarios.json"
    if not path.is_file():
        return ["missing tooling: evaluation/scenarios.json"]

    scenarios, errors = _load_json_array(path, "evaluation corpus")
    if errors:
        return errors

    seen: set[str] = set()
    covered_decisions: set[str] = set()
    for index, raw in enumerate(scenarios, start=1):
        if not isinstance(raw, dict):
            errors.append(f"evaluation scenario #{index} must be an object")
            continue
        scenario: Mapping[str, Any] = raw
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            errors.append(f"evaluation scenario #{index} needs a non-empty id")
            continue
        if scenario_id in seen:
            errors.append(f"duplicate evaluation scenario id: {scenario_id}")
            continue
        seen.add(scenario_id)

        title = scenario.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"evaluation scenario {scenario_id} needs a non-empty title")

        expected = scenario.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"evaluation scenario {scenario_id} needs expected output")
            continue
        expected_decision = expected.get("decision")
        if expected_decision not in DECISIONS:
            errors.append(
                f"evaluation scenario {scenario_id} has invalid expected decision"
            )
            continue
        if not isinstance(expected.get("must_escalate"), bool):
            errors.append(
                f"evaluation scenario {scenario_id} needs boolean expected.must_escalate"
            )
            continue

        covered_decisions.add(expected_decision)
        try:
            actual = route_scenario(scenario)
        except ValueError as exc:
            errors.append(f"evaluation scenario {scenario_id} is invalid: {exc}")
            continue
        if (
            actual.decision != expected_decision
            or actual.must_escalate != expected["must_escalate"]
        ):
            errors.append(
                f"evaluation scenario {scenario_id} expected "
                f"{expected_decision}/{expected['must_escalate']} but policy returned "
                f"{actual.decision}/{actual.must_escalate}"
            )

    missing_decisions = DECISIONS - covered_decisions
    if missing_decisions:
        errors.append(
            "evaluation corpus does not cover decision(s): "
            + ", ".join(sorted(missing_decisions))
        )
    return errors


def validate_ci_policy(root: Path) -> list[str]:
    """Keep unit tests primary, benchmark timing local-only, and actions immutable."""

    workflow = root / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        return ["missing tooling: .github/workflows/ci.yml"]

    try:
        text = workflow.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read CI workflow: {exc}"]

    errors: list[str] = []
    required_commands = {
        "python -m unittest discover": "CI must run the dependency-free unit test suite",
        "python scripts/validate.py": "CI must validate repository structure",
        "python scripts/evaluate.py": "CI must evaluate the deterministic routing corpus",
    }
    for command, message in required_commands.items():
        if command not in text:
            errors.append(message)
    if "benchmark.py" in text:
        errors.append("CI must not run local performance benchmarks")
    if "smoke_test.py" in text:
        errors.append("CI must keep installation smoke tests as explicit local checks")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:"):
            continue
        action = stripped.removeprefix("uses:").strip().split()[0]
        if action.startswith("./") or action.startswith("docker://"):
            continue
        if "@" not in action:
            errors.append("CI actions must be pinned to a full commit SHA: " + stripped)
            continue
        reference = action.rsplit("@", 1)[1]
        if not re.fullmatch(r"[0-9a-fA-F]{40}", reference):
            errors.append(
                "CI actions must be pinned to a full commit SHA: " + stripped
            )
    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    """Validate canonical content, provider entrypoints, and quality tooling."""

    root = Path(root).expanduser()
    canonical = root / "skills" / NAME
    errors = validate_skill_tree(canonical)
    errors.extend(validate_codex_plugin(root))
    errors.extend(validate_evaluation_corpus(root))
    errors.extend(validate_ci_policy(root))

    canonical_reference = f"skills/{NAME}/SKILL.md"
    entrypoints = (
        root / ".agents" / "skills" / NAME / "SKILL.md",
        root / ".claude" / "skills" / NAME / "SKILL.md",
    )
    for entrypoint in entrypoints:
        errors.extend(validate_frontmatter(entrypoint, root))
        if not entrypoint.is_file():
            continue
        try:
            text = entrypoint.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {display_path(entrypoint, root)}: {exc}")
            continue
        if canonical_reference not in text:
            errors.append(
                "provider entrypoint does not reference canonical skill: "
                f"{display_path(entrypoint, root)}"
            )
        if len(text) >= 5_000:
            errors.append(
                "provider entrypoint is too large to remain a thin wrapper: "
                f"{display_path(entrypoint, root)}"
            )

    for relative in REPOSITORY_TOOLING:
        if not (root / relative).is_file():
            errors.append(f"missing tooling: {relative}")

    skill_file = canonical / "SKILL.md"
    if skill_file.is_file():
        try:
            skill_text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            pass
        else:
            pattern = (
                r"implementation complexity.*reasoning depth.*risk.*ambiguity.*"
                r"domain familiarity"
            )
            if not re.search(pattern, skill_text, re.IGNORECASE | re.DOTALL):
                errors.append("canonical skill missing five-dimensional routing statement")

    return errors


def collect_errors(root: Path = ROOT) -> list[str]:
    """Compatibility name used by tests and benchmarks."""

    return validate_repository(root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root to validate.",
    )
    target.add_argument(
        "--skill-root",
        type=Path,
        help="Installed canonical skill directory to validate.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = (
        validate_skill_tree(args.skill_root)
        if args.skill_root
        else validate_repository(args.root)
    )

    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    target = args.skill_root or args.root
    print(f"OK: engineering-agent-hierarchy structure is valid ({target})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
