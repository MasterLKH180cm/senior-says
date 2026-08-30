# Evaluation methodology

The repository has two distinct evaluation layers. They must not be conflated.

## 1. Deterministic routing-policy evaluation

`evaluation/scenarios.json` contains representative engineering tasks with explicit
reasoning-depth, risk, ambiguity, implementation-complexity, domain-familiarity,
and escalation signals. `scripts/policy.py` is a small reference oracle for the
routing defaults documented by the skill.

Run:

```bash
python scripts/evaluate.py
```

This catches drift between the documented routing model, scenario corpus, and
expected ownership decisions. It is deterministic and free of model/API cost.
It is **not** evidence that Codex or Claude will always follow the skill.

## 2. Live provider evaluation

Generate a provider-neutral prompt pack:

```bash
python scripts/evaluate.py \
  --write-prompt-pack artifacts/provider-prompt-pack.json
```

Run that prompt pack in an authenticated Codex or Claude Code session with the
installed skill enabled. Save the model response in the response shape included
in the prompt pack, then score it:

```bash
python scripts/evaluate.py \
  --responses artifacts/provider-responses.json \
  --output artifacts/provider-evaluation.json
```

Keep Codex and Claude results in separate files. Record provider version, model,
reasoning effort, date, and whether the skill was explicitly invoked or selected
automatically. Do not compare scores without those dimensions.

Live provider execution requires an installed/authenticated provider CLI or API
credentials. The repository deliberately does not read, store, or print keys.

## Local performance benchmark

```bash
python scripts/benchmark.py --iterations 50 --warmup 5 --json artifacts/benchmark-local.json
```

The benchmark measures repository validation, deterministic scenario evaluation,
fresh dual-provider installation, and forced dual-provider replacement. Timing
results are environment-specific; use them as before/after evidence, not universal
performance claims. The benchmark is intentionally local-only; CI does not run or
enforce performance timings on shared runners.
