# senior-says

> **When the junior agent gets in over its head, senior says what happens next.**

`senior-says` is a cross-provider engineering skill for coordinating
high-reasoning and faster/lower-cost AI agents as a software delivery team in
Codex and Claude Code.

It is not a generic "spawn more agents" prompt. It defines who may make which
engineering decisions, when a worker must escalate, how work should be bounded,
and who owns the truthfulness of the final result.

**Status:** private beta. The workflow, installer, validation, and deterministic
routing policy are tested. Live Codex/Claude quality and cost improvements still
need task-level provider evaluation.

## Quick start

Clone the repository, inspect the planned destinations, then install the canonical
skill for one or both providers:

```bash
git clone https://github.com/MasterLKH180cm/senior-says.git
cd senior-says

python scripts/install.py both --dry-run
python scripts/install.py both
```

Run the isolated installation smoke test without touching your real user home:

```bash
python scripts/smoke_test.py
```

Try a representative routing decision:

```bash
python scripts/trial.py --list
python scripts/trial.py one-line-auth-change
```

The repository/package/plugin is named **`senior-says`**. The installed compatibility
skill ID is **`engineering-agent-hierarchy`**, so existing Codex and Claude skill
paths remain stable:

```text
~/.agents/skills/engineering-agent-hierarchy
~/.claude/skills/engineering-agent-hierarchy
```

## Why this exists

Model cost and model capability are not the same as task size.

A deterministic rename across 200 files may be large but shallow. A one-line
authorization change may be tiny but require system-level reasoning about privilege,
tenancy, audit, compatibility, and rollback.

`senior-says` therefore routes work using five dimensions:

> **Implementation complexity × reasoning depth × risk × ambiguity × domain familiarity**

The goal is to concentrate expensive reasoning where it changes correctness while
letting bounded execution move quickly.

## Roles

| Role | Primary responsibility |
|---|---|
| **HIGH / Senior Orchestrator** | Problem definition, invariants, architecture, risk, ambiguity, task decomposition, escalation decisions, integration, and final readiness |
| **LOW / Junior Executor** | Bounded implementation, mechanical work, focused discovery, targeted tests, and evidence gathering inside explicit guardrails |
| **REVIEW / Independent Reviewer** | Fresh-context, defect-first review without inheriting the implementer's assumptions |

Model IDs are deliberately not hard-coded. Map these semantic roles to models that
are actually available in the current Codex or Claude environment.

## Reasoning ladder

| Level | Core question | Default ownership |
|---|---|---|
| **R1 — Implementation** | How do I write it? | LOW |
| **R2 — Correctness** | Is it actually correct across inputs and edge cases? | LOW, with HIGH review |
| **R3 — Component design** | Is this a sound local abstraction and interface? | LOW with HIGH guardrails/checkpoints |
| **R4 — System reasoning** | What happens across services, failures, security boundaries, deployment, and rollback? | HIGH |
| **R5 — Problem/organizational reasoning** | Are we solving the right problem, and can an entire class of problems be removed? | HIGH |

Lines of code are not a reasoning metric.

## Execution depth

Routing ownership and process depth are related, but they are not identical. The
authoritative execution contract defines three practical paths:

| Path | Typical work | Default behavior |
|---|---|---|
| **Fast** | Documentation, copy/style changes, test-only changes, deterministic mechanical edits | Focused read, minimal change, one targeted check, manual diff review; no subagent by default |
| **Standard** | Ordinary production behavior, local API/UI state, normal bug fixes | Regression or verification-first evidence, 1–3 targeted checks, consolidated final review; delegate only when work is genuinely independent |
| **High-risk** | Auth, permissions, secrets, migrations, public contracts, concurrency, retry/idempotency, irreversible workflows | HIGH owns the critical decisions; bounded implementation may be delegated; focused security/contract evidence is required |

This keeps small tasks small instead of forcing every change through the full
orchestration ceremony.

## Routing outcomes

The deterministic reference policy uses these outcomes:

| Decision | Meaning |
|---|---|
| `LOW_OWNS` | LOW can complete the bounded task independently; HIGH reviews the result |
| `LOW_WITH_HIGH_GUARDRAILS` | LOW leads implementation under explicit HIGH constraints/checkpoints |
| `HIGH_DECIDES_LOW_EXECUTES` | HIGH resolves system-level decisions, then LOW may implement a bounded packet |
| `HIGH_OWNS` | The operation or decision is too risky/irreversible to delegate |
| `REVIEW_OWNS` | A fresh independent reviewer owns the defect-first review |
| `BLOCKED_DECISION` | A security, behavior, or public-contract ambiguity must be resolved rather than guessed |

Example:

```text
Change one authorization condition
→ R4 + high risk + authorization trigger
→ HIGH_DECIDES_LOW_EXECUTES
→ escalation required
```

```text
Perform a deterministic rename across 200 files
→ R2 + low risk + low ambiguity
→ LOW_OWNS
→ no escalation required
```

## Workflow

1. HIGH frames `Goal / Context / Constraints / Done when / Non-goals`.
2. HIGH classifies reasoning depth, risk, ambiguity, and domain familiarity.
3. HIGH selects the smallest sufficient execution path.
4. HIGH decomposes the work into independently reviewable increments when needed.
5. LOW receives a bounded work packet with ownership, guardrails, acceptance
   criteria, validation, and escalation triggers.
6. LOW implements without silently widening scope and returns evidence.
7. LOW escalates when the packet no longer covers the real problem.
8. HIGH resolves the decision, narrows/upgrades the packet, and integrates the
   actual change.
9. REVIEW performs a fresh-context pass when risk or independence justifies it.
10. HIGH owns final validation, code review, bad-smell review, focused-security
    review, Git/PR truth, and completion status.

> **Senior thinks deeply. Junior moves quickly. Junior asks when the map stops
> matching the terrain. Senior steps in before the blast radius does.**

## Mandatory escalation triggers

LOW must return control instead of guessing when it discovers an unapproved change
to any of the following:

- authentication, authorization, isolation, secrets, PHI/sensitive data, or a
  trust boundary;
- public API, shared schema, or cross-service contract;
- migration ordering/history or destructive data behavior;
- concurrency, retry, idempotency, ordering, transaction boundaries, or
  distributed consistency;
- an irreversible or production operational action;
- ambiguity that changes security, externally visible behavior, or compatibility;
- file/core-logic ownership assigned to another writer;
- evidence that contradicts a packet invariant;
- signs that the requested mechanism solves the wrong problem;
- repeated workaround-on-workaround attempts without a root-cause explanation.

Escalation should be concise:

```text
Observation
Evidence
Why the current packet is insufficient
Decision needed
Safe next options
```

Escalation is a control mechanism, not a failure.

## When it is useful

`senior-says` is most useful for:

- multi-repository delivery;
- auth/authz and security-sensitive changes;
- migrations and deployment controls;
- shared contracts and producer/consumer versioning;
- concurrency, retry, idempotency, and reconciliation;
- long tasks with separable discovery, implementation, validation, and review;
- large mechanical work that should not consume the strongest model;
- teams that need explicit scope, escalation, and reviewer ownership.

It is usually unnecessary for:

- a typo or copy-only change;
- a clearly bounded single-file edit with no shared behavior;
- environments without subagents or per-agent model selection;
- tasks where orchestration overhead is greater than the implementation itself.

Use the Fast path instead of forcing hierarchy into every request.

## Installation

Install for one provider:

```bash
python scripts/install.py codex
python scripts/install.py claude
```

Install both:

```bash
python scripts/install.py both
```

Useful safety/testing options:

```bash
python scripts/install.py both --home /tmp/senior-says-home --dry-run
python scripts/install.py both --home /tmp/senior-says-home
python scripts/install.py both --home /tmp/senior-says-home --force
```

The installer:

- preflights every destination before mutation;
- stages all requested provider copies before replacement;
- refuses unexpected overwrite unless `--force` is explicit;
- rejects source/destination overlap and symlink replacement;
- rolls back previous copies after a partial multi-provider failure;
- performs filesystem-only operations and does not read credentials or execute
  provider commands.

## Codex

The repository root is a skill-only Codex plugin through
`.codex-plugin/plugin.json`, with `skills/` as the skill surface. A direct
`.agents/skills/...` wrapper and the user-level installer remain available as
portable compatibility paths.

Suggested mapping:

- `HIGH_TIER`: strongest suitable coding/reasoning model; high/xhigh reasoning.
- `LOW_TIER`: faster/lower-cost coding-capable model; low/medium reasoning.
- `REVIEW_TIER`: independent capable model, preferably read-only where supported.

See `examples/codex/agents/`.

## Claude Code

Claude Code can use the repository entrypoint under
`.claude/skills/engineering-agent-hierarchy/SKILL.md` or the installed user-level
copy.

Suggested mapping:

- `HIGH_TIER`: Opus-class model.
- `LOW_TIER`: Sonnet-class model for ordinary implementation; use a cheaper tier
  only for genuinely mechanical/bounded work.
- `REVIEW_TIER`: an independent capable reviewer chosen according to risk.

See `examples/claude/agents/`.

## Test and validate

The default toolchain has no third-party Python dependency. Unit tests are the
primary automated test layer:

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/evaluate.py
```

CI runs the unit suite, structural validator, and deterministic routing evaluation
on Linux and Windows across supported Python versions.

## Try it locally

Run an isolated installation lifecycle:

```bash
python scripts/smoke_test.py
```

Inspect individual routing cases:

```bash
python scripts/trial.py --list
python scripts/trial.py docs-typo
python scripts/trial.py component-refactor
python scripts/trial.py one-line-auth-change
```

These commands verify packaging, filesystem installation, and the deterministic
routing contract. They do not invoke a live Codex or Claude model.

## Evaluation

### Deterministic policy regression

```bash
python scripts/evaluate.py --format json --output artifacts/evaluation.json
```

This catches drift between the documented routing model, scenario corpus, and
reference policy. It is fast, deterministic, and free of model/API cost.

It is **not** proof that a live model will follow the skill.

### Live provider evaluation

Generate a provider-neutral prompt pack:

```bash
python scripts/evaluate.py \
  --write-prompt-pack artifacts/provider-prompt-pack.json
```

Run it in an authenticated Codex or Claude session with the skill enabled, save the
structured response, then score it:

```bash
python scripts/evaluate.py \
  --responses artifacts/provider-responses.json \
  --output artifacts/provider-evaluation.json
```

Keep provider/model/reasoning-effort results separate. For real efficacy testing,
also record task completion, blocking defects, scope drift, escalation quality,
high-tier usage, total usage, wall-clock duration, human intervention, and PR
review rounds.

## Local-only benchmark

```bash
python scripts/benchmark.py \
  --iterations 50 \
  --warmup 5 \
  --json artifacts/benchmark-local.json
```

The benchmark records median, p95, min, and max runtime for:

- repository validation;
- deterministic routing evaluation;
- fresh Codex + Claude installation;
- forced dual-provider replacement.

Results are machine- and filesystem-specific. Use them as before/after evidence,
not as universal performance claims. Timing benchmarks intentionally do not run as
CI merge gates and do not measure model inference quality, token consumption, or
end-to-end task completion.

## Current limitations

- HIGH/LOW/REVIEW are semantic roles; enforcement depends on the provider harness.
- Some environments cannot choose a different model per subagent.
- A large execution contract can add context overhead if loaded for trivial work;
  use the Fast path and only open the references required by the current risk.
- HIGH can become a coordination bottleneck if too many workers escalate at once.
- Independent review can duplicate HIGH's review unless reserved for cases where a
  fresh context materially improves confidence.
- Deterministic routing tests validate the specification, not live model adherence.
- No claim of cost, speed, or defect-rate improvement should be made without a
  controlled task-level comparison.

## Repository layout

```text
.codex-plugin/plugin.json                           # Codex skill-only plugin manifest
skills/engineering-agent-hierarchy/
├── SKILL.md                                        # provider-neutral canonical skill
└── references/
    ├── reasoning-depth-and-routing.md
    ├── delegation-and-escalation-protocol.md
    ├── work-packet-template.md
    ├── review-and-integration-protocol.md
    └── development-execution-contract.md

.agents/skills/engineering-agent-hierarchy/SKILL.md # direct Codex entrypoint
.claude/skills/engineering-agent-hierarchy/SKILL.md # Claude Code entrypoint
examples/codex/agents/                              # Codex role examples
examples/claude/agents/                             # Claude role examples
evaluation/scenarios.json                           # deterministic routing corpus
scripts/install.py                                  # transactional local installer
scripts/validate.py                                 # structural/manifest validator
scripts/evaluate.py                                 # reference/provider scoring harness
scripts/trial.py                                    # inspect one routing scenario
scripts/benchmark.py                                # local-only tooling benchmark
scripts/smoke_test.py                               # isolated installation lifecycle
tests/                                              # dependency-free unit tests
```

There is one provider-neutral canonical skill. Provider entrypoints remain thin so
Codex and Claude do not drift into competing workflows.

## GitHub Flow

Development happens on short-lived feature/fix branches and enters `master`
through a pull request. CI provides broad cross-platform regression evidence;
installation smoke tests, provider trials, and timing benchmarks remain explicit
local checks.

See `CONTRIBUTING.md` and `.github/pull_request_template.md`.

## Execution principles

- Delivery first; avoid process theatre.
- Use the smallest sufficient execution path.
- No nested subagents.
- Parallel writers require disjoint ownership.
- LOW does not silently widen scope.
- HIGH does not monopolize mechanical implementation.
- Escalation is a control mechanism, not a failure.
- Tests are evidence, not ritual.
- Review comments are an inbox, not background noise.
- Never claim tests, reviews, pushes, approvals, or merges that did not happen.
- Never auto-merge unless explicitly requested and all repository gates are
  satisfied.

The authoritative delivery/review contract lives at
`skills/engineering-agent-hierarchy/references/development-execution-contract.md`.

## License

MIT
