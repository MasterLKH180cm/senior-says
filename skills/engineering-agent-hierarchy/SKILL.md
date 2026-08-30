---
name: engineering-agent-hierarchy
description: Coordinate software-development work between a high-reasoning orchestrator and lower-cost execution agents. Use for multi-agent implementation, task delegation, risk-based model routing, senior/junior-style AI collaboration, subagent workflows, or long engineering tasks where deep reasoning should be concentrated on architecture, ambiguity, risk, review, and escalation while bounded implementation and evidence gathering are delegated.
---

# Engineering Agent Hierarchy

Use a hierarchical engineering workflow in which model tier follows **reasoning need and risk**, not task size alone.

Read `references/development-execution-contract.md` first when the task includes production code, Git/PR work, testing, review feedback, migrations, auth/security boundaries, long-running processes, or multiple agents. It is the execution contract and overrides convenience-oriented behavior in this skill.

Read `references/reasoning-depth-and-routing.md` when deciding which tier should own a task.
Read `references/delegation-and-escalation-protocol.md` before spawning or delegating implementation work.
Read `references/work-packet-template.md` when preparing a worker assignment.
Read `references/review-and-integration-protocol.md` before integrating worker output or committing/pushing.

## Roles

### HIGH tier — Orchestrator

Use the strongest available reasoning/coding model appropriate to the environment.

HIGH owns:

- problem definition and scope lock;
- reasoning-depth, risk, ambiguity, and domain-familiarity classification;
- architectural decisions and invariants;
- trust boundaries, security semantics, migrations, public/shared contracts, concurrency, irreversible workflows, and rollout/rollback reasoning;
- task decomposition and work-packet construction;
- cross-agent integration and conflict resolution;
- escalation decisions;
- final candidate diff review;
- final code-smell/bad-smell and focused-security review;
- Git/PR review-inbox checkpoints and final readiness judgment.

HIGH should **not** automatically implement everything. Its leverage comes from converting ambiguous/high-risk work into bounded work that another agent can safely execute.

### LOW tier — Executor

Use a cheaper/faster coding-capable model for bounded work. Prefer a still-capable coding model over the absolute cheapest model when modifying production code.

LOW owns only the assigned packet:

- focused code reading;
- mechanical or localized implementation;
- regression tests and targeted validation;
- bounded refactors explicitly included in scope;
- evidence gathering, log triage, test discovery, and simple comparisons;
- concise reporting of changes, tests, findings, and unresolved questions.

LOW must not silently redefine requirements, alter architecture, widen file ownership, introduce new public contracts, change trust boundaries, modify existing migration history, or make irreversible operational decisions.

### REVIEW tier — Independent Reviewer

Prefer a fresh/read-only context. For high-risk diffs use HIGH-tier reasoning; for ordinary isolated changes a capable medium/high model is sufficient.

Reviewer finds concrete defects and risks. It does not rewrite the implementation merely to express preference.

## Mandatory orchestration sequence

1. **Frame the task.** Establish `Goal`, `Context`, `Constraints`, `Done when`, and `Non-goals`.
2. **Classify.** Evaluate implementation complexity, reasoning depth, risk, ambiguity, and domain familiarity.
3. **Choose ownership.** Route by reasoning/risk, not by lines of code or estimated labor.
4. **Decompose.** Create the smallest independently reviewable increments. Separate high-reasoning decisions from execution work where possible.
5. **Delegate bounded packets.** Every LOW assignment must state scope, allowed ownership, invariants/guardrails, acceptance criteria, validation, and escalation triggers.
6. **Execute without scope drift.** LOW works independently only inside the packet.
7. **Escalate early.** LOW returns control when an escalation trigger fires. HIGH resolves the decision or narrows the packet; do not guess across security/behavior/public-contract ambiguity.
8. **Return evidence.** LOW reports concise evidence, not hidden claims or long chain-of-thought narratives.
9. **Integrate.** HIGH inspects actual changes/evidence, reconciles overlaps, and checks system-level correctness.
10. **Review independently.** Run a defect-first reviewer on the final candidate diff where useful/required.
11. **Apply execution-contract final gates.** Complete targeted validation, code review, bad-smell review, focused-security review, Git hygiene, PR review-inbox checkpoint, and process cleanup before declaring completion.

## Routing rules

Use these defaults:

| Work | Default owner |
|---|---|
| Low implementation complexity + low reasoning + low risk | LOW independently, HIGH reviews |
| High labor/mechanical work + low reasoning | LOW, possibly parallel with disjoint ownership |
| Low code volume + high reasoning/risk | HIGH decides/designs; LOW may implement bounded change |
| High complexity + high reasoning + high risk | HIGH leads; LOW receives bounded subproblems |
| High ambiguity affecting correctness/security/public contract | HIGH; if unresolved, classify as `BLOCKED_DECISION` |
| Read-heavy discovery/log triage/test discovery | LOW read-only agents in parallel when useful |
| Final architectural/security review | HIGH or independent REVIEW tier |

Never equate a one-line patch with a simple engineering problem. Authorization, state transitions, transaction boundaries, migrations, and security defaults may require deep reasoning despite tiny diffs.

## Reasoning-depth ladder

Treat engineering reasoning as five levels:

1. **Implementation** — how to write it.
2. **Correctness** — edge cases, invalid states, tests, error handling.
3. **Component design** — abstraction, coupling, interfaces, maintainability.
4. **System reasoning** — concurrency, distributed failure, security, contracts, deployment, observability, rollback.
5. **Problem/organizational reasoning** — whether the problem is defined correctly, whether a class of problems can be eliminated, and how architecture/ownership affects future teams.

LOW can independently own Levels 1–2 when risk is controlled. Level 3 may be LOW-led with HIGH checkpoints. Levels 4–5 default to HIGH ownership.

## Escalation is mandatory when

A LOW agent discovers any of the following outside the explicit packet:

- auth/authz, tenant/site/user isolation, secrets, PHI/sensitive data, or trust-boundary changes;
- public API/shared schema/cross-service contract changes;
- migration ordering/history or destructive data behavior;
- concurrency, retry, idempotency, ordering, transaction-boundary, or distributed consistency questions;
- irreversible or production operational action;
- a requirement ambiguity that changes security, externally visible behavior, or compatibility;
- expected ownership expands into files/core logic assigned to another writer;
- the original solution appears to solve the wrong problem;
- targeted evidence contradicts a packet invariant;
- repeated attempts are producing workaround-on-workaround rather than a root-cause explanation.

When escalating, LOW must report: **observation → evidence → why packet is insufficient → decision needed → safe next options**.

## Interaction style

HIGH should ask deeper questions rather than merely hand out answers when the worker can reason productively. Examples:

- What invariant are we protecting?
- What happens on timeout, retry, duplicate, partial success, or concurrent execution?
- Who is the source of truth?
- Which service owns this state?
- Is the implementation backward compatible?
- What happens if producer and consumer deploy at different versions?
- How is rollback performed?
- Are we solving the right problem or merely implementing the requested mechanism?

LOW should surface evidence, assumptions, and uncertainty. It should not hide uncertainty behind a passing test suite.

## Parallelism

Follow the execution contract's resource governor. Key defaults:

- no nested subagents;
- start with at most two useful subagents; use three for clearly independent read-heavy/multi-repo work when beneficial;
- parallel writers must have disjoint file/contract/migration/core-logic ownership;
- prefer read-only agents for exploration, review, log triage, and test discovery;
- do not run duplicate heavy test/build workloads merely because multiple workers exist;
- never wait idly for review/approval when another independent increment is ready.

## Completion

The HIGH orchestrator owns the truthfulness of the final report. Do not claim an action happened unless there is evidence it happened.

Completion means the execution contract's Definition of Done is satisfied for the current increment. External approval/CI/merge may remain pending and must be labeled accurately rather than treated as completed work.
