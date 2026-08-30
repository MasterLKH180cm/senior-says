#!/usr/bin/env python3
"""Deterministic reference policy for senior-says routing scenarios.

This module is a test oracle for the documented routing defaults. It does not
attempt to emulate a language model or replace engineering judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

DECISIONS = frozenset(
    {
        "LOW_OWNS",
        "LOW_WITH_HIGH_GUARDRAILS",
        "HIGH_DECIDES_LOW_EXECUTES",
        "HIGH_OWNS",
        "REVIEW_OWNS",
        "BLOCKED_DECISION",
    }
)

HIGH_IMPACT_TRIGGERS = frozenset(
    {
        "auth",
        "authorization",
        "security",
        "trust_boundary",
        "public_contract",
        "cross_service_contract",
        "migration",
        "concurrency",
        "retry_idempotency",
        "data_integrity",
        "irreversible_operation",
        "wrong_problem",
    }
)

HIGH_OWNERSHIP_TRIGGERS = frozenset(
    {
        "irreversible_operation",
        "destructive_migration",
        "production_rollback",
    }
)

ALLOWED_TRIGGERS = HIGH_IMPACT_TRIGGERS | HIGH_OWNERSHIP_TRIGGERS
HIGH_IMPACT_AMBIGUITY = frozenset({"correctness", "security", "public_contract"})
ALLOWED_AMBIGUITY_AFFECTS = HIGH_IMPACT_AMBIGUITY


@dataclass(frozen=True)
class RoutingDecision:
    """A deterministic ownership recommendation for one structured scenario."""

    decision: str
    must_escalate: bool
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "must_escalate": self.must_escalate,
            "rationale": list(self.rationale),
        }


def _require_choice(value: Any, field: str, choices: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ValueError(f"{field} must be one of {sorted(choices)}")
    return value


def _string_set(
    value: Any,
    field: str,
    *,
    allowed: frozenset[str],
) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be an array of strings")

    items = set(value)
    unknown = items - allowed
    if unknown:
        raise ValueError(f"{field} contains unsupported value(s): {', '.join(sorted(unknown))}")
    return items


def route_scenario(scenario: Mapping[str, Any]) -> RoutingDecision:
    """Route one structured scenario according to the skill's default policy."""

    work_type = _require_choice(
        scenario.get("work_type", "implementation"),
        "work_type",
        frozenset({"implementation", "review", "discovery"}),
    )
    complexity = _require_choice(
        scenario.get("implementation_complexity"),
        "implementation_complexity",
        frozenset({"low", "medium", "high"}),
    )
    risk = _require_choice(
        scenario.get("risk"),
        "risk",
        frozenset({"low", "medium", "high"}),
    )
    ambiguity = _require_choice(
        scenario.get("ambiguity"),
        "ambiguity",
        frozenset({"low", "medium", "high"}),
    )
    familiarity = _require_choice(
        scenario.get("domain_familiarity"),
        "domain_familiarity",
        frozenset({"low", "medium", "high"}),
    )

    reasoning_depth = scenario.get("reasoning_depth")
    if isinstance(reasoning_depth, bool) or not isinstance(reasoning_depth, int):
        raise ValueError("reasoning_depth must be an integer from 1 to 5")
    if not 1 <= reasoning_depth <= 5:
        raise ValueError("reasoning_depth must be an integer from 1 to 5")

    triggers = _string_set(
        scenario.get("triggers", []),
        "triggers",
        allowed=ALLOWED_TRIGGERS,
    )
    ambiguity_affects = _string_set(
        scenario.get("ambiguity_affects", []),
        "ambiguity_affects",
        allowed=ALLOWED_AMBIGUITY_AFFECTS,
    )

    if work_type == "review":
        return RoutingDecision(
            "REVIEW_OWNS",
            False,
            ("independent final review belongs to the REVIEW tier",),
        )

    if ambiguity == "high" and ambiguity_affects & HIGH_IMPACT_AMBIGUITY:
        return RoutingDecision(
            "BLOCKED_DECISION",
            True,
            ("high-impact ambiguity must be resolved by HIGH rather than guessed",),
        )

    ownership_triggers = triggers & HIGH_OWNERSHIP_TRIGGERS
    if ownership_triggers:
        return RoutingDecision(
            "HIGH_OWNS",
            True,
            (
                "HIGH ownership trigger(s): "
                + ", ".join(sorted(ownership_triggers)),
            ),
        )

    high_triggers = triggers & HIGH_IMPACT_TRIGGERS
    if reasoning_depth >= 4 or risk == "high" or high_triggers:
        reasons: list[str] = []
        if reasoning_depth >= 4:
            reasons.append(f"R{reasoning_depth} system/problem reasoning")
        if risk == "high":
            reasons.append("high blast-radius risk")
        if high_triggers:
            reasons.append(f"escalation trigger(s): {', '.join(sorted(high_triggers))}")
        return RoutingDecision(
            "HIGH_DECIDES_LOW_EXECUTES",
            True,
            tuple(reasons),
        )

    needs_guardrails = (
        reasoning_depth == 3
        or risk == "medium"
        or ambiguity in {"medium", "high"}
        or (familiarity == "low" and complexity != "low")
    )
    if needs_guardrails:
        reasons = []
        if reasoning_depth == 3:
            reasons.append("component-design reasoning needs HIGH guardrails")
        if risk == "medium":
            reasons.append("medium risk needs checkpointed review")
        if ambiguity in {"medium", "high"}:
            reasons.append(f"{ambiguity} ambiguity needs explicit boundaries")
        if familiarity == "low" and complexity != "low":
            reasons.append("low domain familiarity raises execution risk")
        return RoutingDecision(
            "LOW_WITH_HIGH_GUARDRAILS",
            False,
            tuple(reasons),
        )

    return RoutingDecision(
        "LOW_OWNS",
        False,
        ("bounded low-risk work fits LOW ownership",),
    )
