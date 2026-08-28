#!/usr/bin/env python3
"""Run local-only benchmarks for validation, evaluation, and skill installation."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Generic, Sequence, TypeVar

try:
    from scripts.evaluate import evaluate_reference, load_scenarios
    from scripts.install import SOURCE, install_many, provider_destinations
    from scripts.validate import collect_errors
except ModuleNotFoundError:  # Direct execution from scripts/.
    from evaluate import evaluate_reference, load_scenarios
    from install import SOURCE, install_many, provider_destinations
    from validate import collect_errors

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evaluation" / "scenarios.json"
T = TypeVar("T")


@dataclass
class PreparedCase(Generic[T]):
    """State and cleanup callback prepared outside a timed interval."""

    state: T
    cleanup: Callable[[], None]


@dataclass
class InstallFixture:
    temporary_home: tempfile.TemporaryDirectory[str]
    destinations: tuple[Path, ...]

    def cleanup(self) -> None:
        self.temporary_home.cleanup()


def percentile(sorted_values: Sequence[float], value: float) -> float:
    """Return a nearest-rank percentile from an already-sorted sequence."""

    if not sorted_values:
        raise ValueError("cannot calculate percentile of an empty sequence")
    if not 0 < value <= 1:
        raise ValueError("percentile must be greater than 0 and at most 1")
    index = max(0, math.ceil(value * len(sorted_values)) - 1)
    return sorted_values[index]


def summarize(samples_ms: Sequence[float]) -> dict[str, float | int]:
    if not samples_ms:
        raise ValueError("cannot summarize an empty sample set")
    ordered = sorted(samples_ms)
    return {
        "iterations": len(ordered),
        "median_ms": statistics.median(ordered),
        "p95_ms": percentile(ordered, 0.95),
        "min_ms": ordered[0],
        "max_ms": ordered[-1],
    }


def _validate_counts(iterations: int, warmup: int) -> None:
    if iterations < 1 or warmup < 0:
        raise ValueError("iterations must be >= 1 and warmup must be >= 0")


def measure(
    operation: Callable[[], None],
    iterations: int,
    warmup: int,
) -> dict[str, float | int]:
    """Measure an operation whose entire body is intentionally timed."""

    _validate_counts(iterations, warmup)
    for _ in range(warmup):
        operation()

    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return summarize(samples)


def measure_prepared(
    prepare: Callable[[], PreparedCase[T]],
    operation: Callable[[T], None],
    iterations: int,
    warmup: int,
) -> dict[str, float | int]:
    """Measure only the operation while setup and cleanup stay outside timing."""

    _validate_counts(iterations, warmup)
    samples: list[float] = []
    total = iterations + warmup
    for index in range(total):
        case = prepare()
        try:
            started = time.perf_counter_ns()
            operation(case.state)
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        finally:
            case.cleanup()
        if index >= warmup:
            samples.append(elapsed_ms)
    return summarize(samples)


def package_metrics(root: Path) -> dict[str, int]:
    files = [path for path in Path(root).rglob("*") if path.is_file()]
    return {
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def _prepare_fresh_install() -> PreparedCase[InstallFixture]:
    temporary_home = tempfile.TemporaryDirectory(prefix="senior-says-bench-")
    fixture = InstallFixture(
        temporary_home,
        provider_destinations("both", Path(temporary_home.name)),
    )
    return PreparedCase(fixture, fixture.cleanup)


def _prepare_force_install() -> PreparedCase[InstallFixture]:
    case = _prepare_fresh_install()
    try:
        install_many(SOURCE, case.state.destinations)
    except Exception:
        case.cleanup()
        raise
    return case


def run_benchmarks(iterations: int, warmup: int) -> dict[str, object]:
    """Run the complete local benchmark suite."""

    scenarios = load_scenarios(SCENARIOS)

    def validate_operation() -> None:
        errors = collect_errors(ROOT)
        if errors:
            raise RuntimeError(f"repository validation failed: {errors}")

    def evaluate_operation() -> None:
        results = evaluate_reference(scenarios)
        if not all(result.passed for result in results):
            raise RuntimeError("reference-policy evaluation failed")

    def install_fresh(fixture: InstallFixture) -> None:
        install_many(SOURCE, fixture.destinations)

    def install_force(fixture: InstallFixture) -> None:
        install_many(SOURCE, fixture.destinations, force=True)

    return {
        "metadata": {
            "benchmark": "senior-says-local",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "logical_cpus": os.cpu_count(),
            "iterations": iterations,
            "warmup": warmup,
            "package": package_metrics(SOURCE),
            "scenario_count": len(scenarios),
            "scope": "local deterministic tooling only; no model inference",
            "notes": {
                "fresh_install": (
                    "includes copying both provider trees; temporary-home setup is "
                    "outside the timed interval"
                ),
                "force_replace": (
                    "existing provider trees are seeded outside the timed interval; "
                    "only replacement is timed"
                ),
            },
        },
        "operations": {
            "validate_repository": measure(validate_operation, iterations, warmup),
            "evaluate_routing": measure(evaluate_operation, iterations, warmup),
            "install_both_fresh": measure_prepared(
                _prepare_fresh_install,
                install_fresh,
                iterations,
                warmup,
            ),
            "install_both_force_replace": measure_prepared(
                _prepare_force_install,
                install_force,
                iterations,
                warmup,
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--json", type=Path, help="Write benchmark data to this path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_benchmarks(args.iterations, args.warmup)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"BENCHMARK FAIL: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(serialized + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"BENCHMARK FAIL: cannot write {args.json}: {exc}", file=sys.stderr)
            return 1

    print("senior-says local benchmark")
    for name, metrics in report["operations"].items():
        print(
            f"- {name}: median={metrics['median_ms']:.3f} ms, "
            f"p95={metrics['p95_ms']:.3f} ms, max={metrics['max_ms']:.3f} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
