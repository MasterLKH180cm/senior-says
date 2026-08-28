# senior-says

**When the junior agent gets in over its head, senior says what happens next.**

A cross-provider engineering skill for coordinating **high-reasoning** and
**fast/lower-cost** AI agents as a software delivery team for Codex and Claude
Code.

- **HIGH / Senior Orchestrator** owns problem definition, invariants, architecture,
  risk, ambiguity, delegation, escalation, integration, and final readiness.
- **LOW / Junior Executor** owns bounded implementation, mechanical work, focused
  discovery, targeted tests, and evidence gathering inside explicit guardrails.
- **REVIEW / Independent Reviewer** inspects the final candidate diff without
  inheriting the implementer's assumptions.

The routing rule is:

> **Implementation complexity × reasoning depth × risk × ambiguity × domain familiarity**

A one-line authorization change can require R4 system reasoning. A deterministic
200-file rename can remain R1–R2. Lines of code are not a reasoning metric.

## How it works

1. HIGH frames `Goal / Context / Constraints / Done when / Non-goals`.
2. HIGH classifies reasoning depth, risk, ambiguity, and domain familiarity.
3. HIGH decomposes work into independently reviewable increments.
4. LOW receives a bounded work packet with ownership, guardrails, acceptance
   criteria, validation, and escalation triggers.
5. LOW implements without silently widening scope and returns evidence.
6. LOW escalates across trust boundaries, public contracts, migrations,
   concurrency, irreversible operations, or unresolved high-impact ambiguity.
7. HIGH resolves the decision, narrows or upgrades the packet, and integrates the
   result.
8. REVIEW performs an independent defect-first pass.
9. HIGH owns final validation, code review, bad-smell review, focused-security
   review, Git/PR truth, and completion status.

> **Senior thinks deeply. Junior moves quickly. Junior asks when the map stops
> matching the terrain. Senior steps in before the blast radius does.**

## Reasoning ladder

| Level | Question | Default ownership |
|---|---|---|
| R1 — Implementation | How do I write this? | LOW |
| R2 — Correctness | Is it actually correct? | LOW + HIGH review |
| R3 — Component Design | Is this a good local design? | LOW with HIGH guardrails |
| R4 — System Reasoning | What happens across the whole system? | HIGH |
| R5 — Problem / Organizational Reasoning | Are we solving the right problem? | HIGH |

## Repository layout

```text
.codex-plugin/plugin.json                          # Codex skill-only plugin manifest
skills/engineering-agent-hierarchy/
├── SKILL.md                                       # provider-neutral canonical skill
└── references/
    ├── reasoning-depth-and-routing.md
    ├── delegation-and-escalation-protocol.md
    ├── work-packet-template.md
    ├── review-and-integration-protocol.md
    └── development-execution-contract.md

.agents/skills/engineering-agent-hierarchy/SKILL.md # direct Codex entrypoint
.claude/skills/engineering-agent-hierarchy/SKILL.md # Claude Code entrypoint
examples/codex/agents/                              # semantic role examples
examples/claude/agents/                             # semantic role examples
evaluation/scenarios.json                           # deterministic routing corpus
scripts/install.py                                  # transactional local installer
scripts/validate.py                                 # structural and manifest validator
scripts/evaluate.py                                 # reference/provider scoring harness
scripts/trial.py                                    # inspect one routing scenario locally
scripts/benchmark.py                                # local-only performance benchmark
tests/                                              # dependency-free unit tests
```

There is one provider-neutral canonical skill. Provider entrypoints remain thin so
Codex and Claude do not drift into competing workflows.

## Codex

The repository root is a skill-only Codex plugin through
`.codex-plugin/plugin.json`, with `skills/` as its skill surface. The direct
`.agents/skills/...` wrapper and user-level installer remain available as a
portable/manual compatibility path.

Map roles semantically rather than pinning a model ID:

- `HIGH_TIER`: strongest suitable coding/reasoning model; high/xhigh reasoning.
- `LOW_TIER`: faster/lower-cost coding-capable model; low/medium reasoning.
- `REVIEW_TIER`: independent strong model, preferably read-only where supported.

See `examples/codex/agents/`.

## Claude Code

Claude Code can use the project entrypoint at
`.claude/skills/engineering-agent-hierarchy/SKILL.md` or a user-level copy under
`~/.claude/skills/`.

Suggested semantic mapping:

- `HIGH_TIER`: Opus-class model.
- `LOW_TIER`: Sonnet-class for normal implementation; a cheaper tier only for
  genuinely bounded/mechanical work.
- `REVIEW_TIER`: independent capable reviewer selected according to risk.

See `examples/claude/agents/`.

## Local installation

The installer preflights every target, stages copies beside the destination,
refuses unexpected overwrite and symlink replacement, and rolls back a partial
multi-provider installation.

```bash
python scripts/install.py codex
python scripts/install.py claude
python scripts/install.py both
```

Useful test options:

```bash
python scripts/install.py both --home /tmp/senior-says-home
python scripts/install.py both --home /tmp/senior-says-home --force
python scripts/install.py both --home /tmp/senior-says-home --dry-run
```

Existing installs are preserved unless `--force` is explicit.

## Test and validate

The default toolchain has no third-party Python dependency.

```bash
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/evaluate.py
```

The validator checks canonical/provider skill files, frontmatter, references,
Codex plugin metadata, execution-contract markers, and CI policy. The evaluator
checks the routing scenario corpus.

## Try the installed skill locally

Run the isolated smoke test. It installs both provider copies into a disposable
home, validates them, verifies overwrite protection, and exercises forced
replacement without touching your real user directories:

```bash
python scripts/smoke_test.py
```

Then try a representative routing case:

```bash
python scripts/trial.py --list
python scripts/trial.py one-line-auth-change
```

These checks verify packaging, installation, and the deterministic routing contract.
They do not claim live Codex or Claude inference quality; authenticated provider
execution is a separate evaluation step.

## Evaluation

The deterministic corpus verifies the documented routing policy without spending
model tokens:

```bash
python scripts/evaluate.py --format json --output artifacts/evaluation.json
```

To evaluate actual Codex or Claude behavior, generate a prompt pack, run it in an
authenticated provider session with the skill enabled, then score the recorded
JSON response:

```bash
python scripts/evaluate.py \
  --write-prompt-pack artifacts/provider-prompt-pack.json
python scripts/evaluate.py \
  --responses artifacts/provider-responses.json \
  --output artifacts/provider-evaluation.json
```

The deterministic score is a policy regression test, not a claim about live model
quality. See `evaluation/README.md` for the provider evaluation protocol.

## Benchmark

```bash
python scripts/benchmark.py \
  --iterations 50 \
  --warmup 5 \
  --json artifacts/benchmark-local.json
```

The benchmark records median, p95, min, and max runtime for:

- repository validation;
- routing-scenario evaluation;
- fresh Codex + Claude installation;
- forced Codex + Claude replacement.

Results are machine- and filesystem-specific. Use them as before/after evidence.
The benchmark is intentionally local-only and is never executed as a CI merge gate.

## GitHub Flow

Development happens on short-lived feature/fix branches and enters `master`
through a pull request. CI runs dependency-free unit tests across Linux and Windows
on Python 3.10, 3.12, and 3.14, then validates the skill/plugin structure. Local smoke tests,
provider trials, and performance benchmarks remain explicit developer checks rather
than timing-sensitive CI gates.

See `CONTRIBUTING.md` and `.github/pull_request_template.md`.

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
- Never auto-merge unless explicitly requested and all repository gates pass.

The authoritative delivery/review contract lives at
`skills/engineering-agent-hierarchy/references/development-execution-contract.md`.
