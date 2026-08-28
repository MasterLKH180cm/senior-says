# senior-says

**When the junior agent gets in over its head, senior says what happens next.**

A cross-provider engineering skill for coordinating **high-reasoning** and **fast/lower-cost** AI agents as a software delivery team for Codex and Claude Code.

The model is inspired by healthy senior/junior engineering collaboration without assuming that model tier equals human seniority:

- **HIGH tier / Senior Orchestrator** — owns problem definition, scope, invariants, architecture, risk, ambiguity, delegation, escalation, integration, and final review.
- **LOW tier / Junior Executor** — owns bounded implementation, mechanical work, focused discovery, targeted tests, and evidence gathering inside explicit guardrails.
- **REVIEW tier / Independent Reviewer** — independently inspects the final candidate diff and hunts concrete defects without inheriting the implementer's assumptions.

The core rule is not "easy work to cheap models, hard work to expensive models." Routing is based on:

> **Implementation complexity × reasoning depth × risk × ambiguity × domain familiarity**

## How senior-says works

1. HIGH frames `Goal / Context / Constraints / Done when / Non-goals`.
2. HIGH classifies reasoning depth, risk, ambiguity, and domain familiarity.
3. HIGH decomposes the work into independently reviewable increments.
4. LOW receives a bounded work packet with ownership, guardrails, acceptance criteria, validation, and escalation triggers.
5. LOW implements and returns evidence rather than silently widening scope.
6. LOW escalates when the task crosses a trust boundary, public contract, migration, concurrency rule, irreversible operation, or unresolved high-impact ambiguity.
7. HIGH resolves the decision, narrows or upgrades the packet, and integrates the actual changes.
8. REVIEW performs an independent defect-first pass.
9. HIGH owns final validation, code review, bad-smell review, focused-security review, Git/PR truth, and completion status.

In short:

> **Senior thinks deeply. Junior moves quickly. Junior asks when the map stops matching the terrain. Senior steps in before the blast radius does.**

## Reasoning ladder

| Level | Question | Default ownership |
|---|---|---|
| R1 — Implementation | How do I write this? | LOW |
| R2 — Correctness | Is it actually correct? | LOW + HIGH review |
| R3 — Component Design | Is this a good local design? | LOW or HIGH guardrails |
| R4 — System Reasoning | What happens across the whole system? | HIGH |
| R5 — Problem / Organizational Reasoning | Are we solving the right problem? | HIGH |

A one-line authorization change can be R4. A 200-file mechanical migration can be R1–R2. Lines of code are not a reasoning metric.

## Repository layout

```text
skills/engineering-agent-hierarchy/
├── SKILL.md
└── references/
    ├── reasoning-depth-and-routing.md
    ├── delegation-and-escalation-protocol.md
    ├── work-packet-template.md
    ├── review-and-integration-protocol.md
    └── development-execution-contract.md

.agents/skills/engineering-agent-hierarchy/SKILL.md   # Codex repo entrypoint
.claude/skills/engineering-agent-hierarchy/SKILL.md   # Claude Code repo entrypoint
examples/codex/agents/                                # Codex role examples
examples/claude/agents/                               # Claude role examples
scripts/install.py                                    # personal skill installer
scripts/validate.py                                   # structural validation
```

There is one provider-neutral canonical skill. Codex and Claude entrypoints remain deliberately thin so the workflow cannot drift into two competing copies.

## Codex

Codex discovers repository skills under `.agents/skills/<name>/SKILL.md`.

Map the semantic roles to models available in the current environment:

- `HIGH_TIER`: strongest suitable coding/reasoning model; high/xhigh reasoning.
- `LOW_TIER`: faster/lower-cost coding-capable model; low/medium reasoning.
- `REVIEW_TIER`: an independent strong model, preferably read-only where supported.

The skill deliberately does not hard-code a Codex model ID because model availability and account entitlements change.

See `examples/codex/agents/`.

## Claude Code

Claude Code uses the project skill entrypoint under `.claude/skills/<name>/SKILL.md`.

Suggested semantic mapping:

- `HIGH_TIER`: Opus-class model.
- `LOW_TIER`: Sonnet-class model for normal implementation; use a cheaper tier only for genuinely bounded/mechanical work.
- `REVIEW_TIER`: an independent capable reviewer chosen according to risk.

See `examples/claude/agents/`.

## Personal installation

Install the canonical skill for one or both providers:

```bash
python scripts/install.py codex
python scripts/install.py claude
python scripts/install.py both
```

Existing installs are preserved unless `--force` is explicitly supplied.

## Execution philosophy

- Delivery first; avoid process theatre.
- No nested subagents.
- Parallel writers require disjoint ownership.
- LOW does not silently widen scope.
- HIGH does not monopolize implementation.
- Escalation is a control mechanism, not a failure.
- Tests are evidence, not ritual.
- Review comments are an inbox, not background noise.
- Never claim tests, reviews, pushes, approvals, or merges that did not happen.
- Never auto-merge unless explicitly requested and all repository gates are satisfied.

The full delivery/review contract lives at `skills/engineering-agent-hierarchy/references/development-execution-contract.md`.

## Validate

```bash
python scripts/validate.py
```

The validator checks required skill files, YAML frontmatter, provider entrypoints, and the canonical execution-contract reference.
