# Work Packet Template

Use this template when HIGH delegates to a LOW agent.

```markdown
## Objective
<one bounded outcome>

## Context
<only the context necessary to execute safely>

## Ownership
Allowed:
- <files/directories/functions/workstream>

Do not modify:
- <protected files/contracts/migrations/core logic>

## Invariants / Guardrails
- <must remain true>
- <must not change>
- <compatibility/security constraints>

## Acceptance Criteria
- [ ] <observable result>
- [ ] <observable result>

## Validation
Run the smallest relevant checks:
- <targeted test/command>
- <targeted test/command>

Do not run broad/full suites unless the evidence requires them.

## Escalate Instead of Guessing If
- <task-specific trigger>
- auth/security/public contract/migration/concurrency/irreversible behavior changes
- ownership expands outside the packet
- evidence contradicts an invariant

## Return
- summary of change
- exact files changed
- tests/commands + results
- evidence
- unresolved risks/questions
```

## Good packet characteristics

A good packet gives the worker enough context to make local implementation decisions while keeping system-level decisions with HIGH.

Bad packet:

> Fix the reporting architecture and tests.

Better packet:

> Update only `report_serializer.py` and its unit tests so the existing v2 contract emits the already-defined `author_id` field. Do not change schema/version/auth semantics. Escalate if the current model cannot represent the required field without a contract change.
