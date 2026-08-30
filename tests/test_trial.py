from __future__ import annotations

import contextlib
import io
import unittest

from scripts import evaluate, trial


class TrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = evaluate.load_scenarios(evaluate.DEFAULT_SCENARIOS)

    def test_find_scenario_returns_known_case(self) -> None:
        scenario = trial.find_scenario(self.scenarios, "one-line-auth-change")
        self.assertIsNotNone(scenario)
        self.assertEqual(scenario["title"], "Change one authorization condition")

    def test_known_scenario_matches_expected_decision(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = trial.main(["one-line-auth-change"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Decision: HIGH_DECIDES_LOW_EXECUTES", output.getvalue())

    def test_unknown_scenario_is_rejected(self) -> None:
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            exit_code = trial.main(["not-a-scenario"])
        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown scenario", error.getvalue())


if __name__ == "__main__":
    unittest.main()
