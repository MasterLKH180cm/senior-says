from __future__ import annotations

import unittest

from scripts.policy import route_scenario


BASE = {
    "work_type": "implementation",
    "implementation_complexity": "low",
    "reasoning_depth": 1,
    "risk": "low",
    "ambiguity": "low",
    "domain_familiarity": "high",
    "triggers": [],
    "ambiguity_affects": [],
}


class PolicyUnitTests(unittest.TestCase):
    def test_low_risk_bounded_work_routes_to_low(self) -> None:
        result = route_scenario(BASE)
        self.assertEqual(result.decision, "LOW_OWNS")
        self.assertFalse(result.must_escalate)

    def test_high_volume_mechanical_work_can_remain_low_owned(self) -> None:
        scenario = {**BASE, "implementation_complexity": "high", "reasoning_depth": 2}
        self.assertEqual(route_scenario(scenario).decision, "LOW_OWNS")

    def test_component_design_routes_to_low_with_high_guardrails(self) -> None:
        scenario = {**BASE, "reasoning_depth": 3}
        self.assertEqual(
            route_scenario(scenario).decision,
            "LOW_WITH_HIGH_GUARDRAILS",
        )

    def test_high_non_contract_ambiguity_uses_guardrails_instead_of_guessing(self) -> None:
        scenario = {**BASE, "ambiguity": "high"}
        self.assertEqual(
            route_scenario(scenario).decision,
            "LOW_WITH_HIGH_GUARDRAILS",
        )

    def test_high_impact_ambiguity_blocks_decision(self) -> None:
        scenario = {
            **BASE,
            "ambiguity": "high",
            "ambiguity_affects": ["security"],
        }
        result = route_scenario(scenario)
        self.assertEqual(result.decision, "BLOCKED_DECISION")
        self.assertTrue(result.must_escalate)

    def test_one_line_auth_change_routes_through_high(self) -> None:
        scenario = {
            **BASE,
            "reasoning_depth": 4,
            "risk": "high",
            "triggers": ["authorization"],
        }
        result = route_scenario(scenario)
        self.assertEqual(result.decision, "HIGH_DECIDES_LOW_EXECUTES")
        self.assertTrue(result.must_escalate)

    def test_irreversible_operation_stays_with_high(self) -> None:
        scenario = {
            **BASE,
            "reasoning_depth": 4,
            "risk": "high",
            "triggers": ["irreversible_operation"],
        }
        result = route_scenario(scenario)
        self.assertEqual(result.decision, "HIGH_OWNS")
        self.assertTrue(result.must_escalate)

    def test_review_routes_to_independent_reviewer(self) -> None:
        scenario = {**BASE, "work_type": "review", "reasoning_depth": 4}
        result = route_scenario(scenario)
        self.assertEqual(result.decision, "REVIEW_OWNS")
        self.assertFalse(result.must_escalate)

    def test_invalid_reasoning_depth_is_rejected(self) -> None:
        for invalid in (True, 0, 6, "4"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "reasoning_depth"):
                    route_scenario({**BASE, "reasoning_depth": invalid})

    def test_trigger_list_must_be_an_array_of_strings(self) -> None:
        with self.assertRaisesRegex(ValueError, "triggers must be an array of strings"):
            route_scenario({**BASE, "triggers": "authorization"})

    def test_unknown_trigger_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            route_scenario({**BASE, "triggers": ["authorizaton"]})

    def test_unknown_ambiguity_effect_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported value"):
            route_scenario({**BASE, "ambiguity_affects": ["performance"]})


if __name__ == "__main__":
    unittest.main()
