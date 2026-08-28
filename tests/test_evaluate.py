from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import evaluate


class EvaluateUnitTests(unittest.TestCase):
    def test_reference_corpus_passes(self) -> None:
        scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)
        results = evaluate.evaluate_reference(scenarios)

        self.assertTrue(results)
        self.assertTrue(all(result.passed for result in results))

    def test_canonical_skill_is_complete(self) -> None:
        self.assertEqual(evaluate.validate_skill_root(evaluate.DEFAULT_SKILL_ROOT), [])

    def test_provider_scoring_detects_wrong_decision(self) -> None:
        scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)[:1]
        responses = {
            scenarios[0]["id"]: {
                "scenario_id": scenarios[0]["id"],
                "decision": "HIGH_OWNS",
                "must_escalate": True,
            }
        }

        results = evaluate.score_provider(scenarios, responses)

        self.assertFalse(results[0].passed)

    def test_provider_scoring_marks_missing_response(self) -> None:
        scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)[:1]

        results = evaluate.score_provider(scenarios, {})

        self.assertFalse(results[0].passed)
        self.assertEqual(results[0].error, "missing response")

    def test_provider_scoring_rejects_unknown_scenario_ids(self) -> None:
        scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)[:1]
        responses = {
            "unknown": {
                "scenario_id": "unknown",
                "decision": "LOW_OWNS",
                "must_escalate": False,
            }
        }

        with self.assertRaisesRegex(ValueError, "unknown scenario"):
            evaluate.score_provider(scenarios, responses)

    def test_prompt_pack_excludes_expected_answers(self) -> None:
        scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)
        with tempfile.TemporaryDirectory(prefix="senior-says-prompt-") as temp_dir:
            output = Path(temp_dir) / "prompt.json"
            evaluate.write_prompt_pack(output, scenarios)
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertTrue(payload["scenarios"])
        self.assertTrue(
            all("expected" not in scenario for scenario in payload["scenarios"])
        )
        self.assertEqual(
            {scenario["id"] for scenario in payload["scenarios"]},
            {scenario["id"] for scenario in scenarios},
        )

    def test_duplicate_scenario_ids_are_rejected(self) -> None:
        scenario = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)[0]
        with tempfile.TemporaryDirectory(prefix="senior-says-scenarios-") as temp_dir:
            path = Path(temp_dir) / "scenarios.json"
            path.write_text(json.dumps([scenario, scenario]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate scenario id"):
                evaluate.load_scenarios(path)

    def test_provider_response_loader_accepts_metadata_wrapper(self) -> None:
        with tempfile.TemporaryDirectory(prefix="senior-says-responses-") as temp_dir:
            path = Path(temp_dir) / "responses.json"
            path.write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "model": "example",
                        "responses": [
                            {
                                "scenario_id": "docs-typo",
                                "decision": "LOW_OWNS",
                                "must_escalate": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            responses = evaluate.load_provider_responses(path)

        self.assertEqual(responses["docs-typo"]["decision"], "LOW_OWNS")

    def test_cli_reports_output_write_failure_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="senior-says-evaluate-output-") as temp:
            parent = Path(temp) / "not-a-directory"
            parent.write_text("file", encoding="utf-8")
            output = parent / "evaluation.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = evaluate.main(["--output", str(output)])

        self.assertEqual(exit_code, 2)
        self.assertIn("cannot write", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
