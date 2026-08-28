from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import benchmark


class BenchmarkUnitTests(unittest.TestCase):
    def test_percentile_uses_nearest_rank(self) -> None:
        self.assertEqual(benchmark.percentile([1.0, 2.0, 3.0, 4.0], 0.95), 4.0)

    def test_percentile_rejects_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            benchmark.percentile([], 0.95)
        with self.assertRaises(ValueError):
            benchmark.percentile([1.0], 0)

    def test_measure_invokes_warmups_and_iterations(self) -> None:
        calls = 0

        def operation() -> None:
            nonlocal calls
            calls += 1

        metrics = benchmark.measure(operation, iterations=3, warmup=2)

        self.assertEqual(calls, 5)
        self.assertEqual(metrics["iterations"], 3)
        self.assertGreaterEqual(metrics["median_ms"], 0)

    def test_measure_prepared_prepares_and_cleans_each_sample(self) -> None:
        prepared: list[int] = []
        operated: list[int] = []
        cleaned: list[int] = []

        def prepare() -> benchmark.PreparedCase[int]:
            value = len(prepared)
            prepared.append(value)
            return benchmark.PreparedCase(value, lambda: cleaned.append(value))

        def operation(value: int) -> None:
            operated.append(value)

        metrics = benchmark.measure_prepared(
            prepare,
            operation,
            iterations=3,
            warmup=2,
        )

        self.assertEqual(prepared, [0, 1, 2, 3, 4])
        self.assertEqual(operated, prepared)
        self.assertEqual(cleaned, prepared)
        self.assertEqual(metrics["iterations"], 3)

    def test_measure_prepared_cleans_after_operation_failure(self) -> None:
        cleaned: list[bool] = []

        def prepare() -> benchmark.PreparedCase[None]:
            return benchmark.PreparedCase(None, lambda: cleaned.append(True))

        def fail(_state: None) -> None:
            raise RuntimeError("boom")

        with self.assertRaisesRegex(RuntimeError, "boom"):
            benchmark.measure_prepared(
                prepare,
                fail,
                iterations=1,
                warmup=0,
            )

        self.assertEqual(cleaned, [True])

    def test_package_metrics_counts_files_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="senior-says-metrics-") as temp:
            root = Path(temp)
            (root / "one.txt").write_text("one", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "two.txt").write_text("two!", encoding="utf-8")

            metrics = benchmark.package_metrics(root)

        self.assertEqual(metrics, {"file_count": 2, "total_bytes": 7})

    def test_cli_reports_output_write_failure_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="senior-says-benchmark-output-") as temp:
            parent = Path(temp) / "not-a-directory"
            parent.write_text("file", encoding="utf-8")
            output = parent / "benchmark.json"
            stderr = io.StringIO()
            with mock.patch(
                "scripts.benchmark.run_benchmarks",
                return_value={"metadata": {}, "operations": {}},
            ), contextlib.redirect_stderr(stderr):
                exit_code = benchmark.main(["--json", str(output)])

        self.assertEqual(exit_code, 1)
        self.assertIn("cannot write", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
