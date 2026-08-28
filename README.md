# Engineering Agent Hierarchy Skill

A cross-provider engineering skill for coordinating **high-reasoning** and **fast/low-cost** AI agents as a software delivery team.

The interaction model is intentionally analogous to senior/junior engineering collaboration without assuming that model tier equals human seniority:

- **HIGH tier / Orchestrator** — owns problem definition, scope, invariants, architecture, risk, delegation, integration, escalation decisions, and final review.
- **LOW tier / Executor** — owns bounded implementation, mechanical work, focused discovery, targeted tests, and evidence gathering inside explicit guardrails.
- **Independent Reviewer** — read-only whenever possible; reviews the final candidate diff or risky delta without inheriting the implementer's assumptions.

The core idea is not "easy work to cheap models, hard work to expensive models." Routing is based on:

> **Implementation complexity × reasoning depth × risk × ambiguity × domain familiarity**

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
examples/codex/agents/                                # semantic role examples
examples/claude/agents/                               # semantic role examples
scripts/validate.py
```

## Codex

Codex discovers repository skills under `.agents/skills/<name>/SKILL.md`. The repo entrypoint redirects to the canonical skill in `skills/engineering-agent-hierarchy/` so there is only one source of truth.

The skill does **not** hard-code a Codex model ID. Model availability varies by account and runtime. Map roles semantically:

- `HIGH_TIER`: strongest coding/reasoning model available; high/xhigh reasoning.
- `LOW_TIER`: cheaper/faster coding-capable model; low/medium reasoning.
- `REVIEW_TIER`: independent strong model or HIGH_TIER in a fresh/read-only role.

See `examples/codex/agents/` for role templates.

## Claude Code

Claude Code discovers project skills under `.claude/skills/<name>/SKILL.md`. The repo entrypoint redirects to the same canonical skill.

Suggested semantic mapping:

- `HIGH_TIER`: Opus-class model.
- `LOW_TIER`: Sonnet-class model for implementation; Haiku-class only for truly mechanical/read-only work.
- `REVIEW_TIER`: Opus-class or an independent Sonnet/Opus reviewer depending on risk.

See `examples/claude/agents/` for role templates.

## Core workflow

1. HIGH tier defines `Goal / Context / Constraints / Done when / Non-goals`.
2. HIGH tier classifies reasoning depth, risk, ambiguity, and domain familiarity.
3. HIGH tier decomposes work into independently reviewable increments.
4. LOW tier receives a bounded **work packet** with file ownership, guardrails, acceptance criteria, tests, and escalation triggers.
5. LOW tier implements and returns concise evidence, not a long narrative.
6. LOW tier escalates immediately when the task crosses a trust boundary, contract, migration, concurrency, irreversible operation, or unresolved ambiguity.
7. HIGH tier integrates the evidence, resolves architectural decisions, and may re-delegate a narrower packet.
8. Independent review checks the final candidate diff.
9. HIGH tier owns final code-review, bad-smell, focused-security, Git/PR, and review-feedback gates.
10. Work stops only at a real external blocker or completed definition of done—not because a worker is waiting for another agent.

## Principles

- Delivery first; avoid process theatre.
- No nested subagents.
- Parallel writes require disjoint file/logic ownership.
- LOW tier agents do not silently widen scope.
- HIGH tier agents do not steal every implementation task.
- Escalation is a normal control mechanism, not a failure.
- Tests are evidence, not ritual.
- Review comments are an inbox that must be re-read at explicit checkpoints.
- Never claim tests, reviews, pushes, approvals, or merges that did not happen.
- Never auto-merge unless the user explicitly requested it and all repository gates are satisfied.

## Validation

Run:

```bash
python scripts/validate.py
```

This verifies required skill files, frontmatter, provider entrypoints, and the canonical execution-contract reference.
