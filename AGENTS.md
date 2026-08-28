# Repository Instructions

This repository contains the canonical `engineering-agent-hierarchy` skill and the
`senior-says` Codex skill-only plugin manifest.

When modifying it:

1. Keep `skills/engineering-agent-hierarchy/SKILL.md` provider-neutral.
2. Keep provider-specific behavior in `.agents/`, `.claude/`, or provider examples.
3. Do not duplicate the full canonical skill into provider entrypoints.
4. Preserve `development-execution-contract.md` as the authoritative delivery and
   review contract unless explicitly asked to revise it.
5. Keep routing changes synchronized with `evaluation/scenarios.json` and
   `scripts/policy.py`; the deterministic policy is an evaluation oracle, not an
   LLM replacement.
6. Use GitHub Flow: short-lived branch, targeted validation, final review, PR to
   `master`; do not develop directly on `master`.
7. Before completion run:

```bash
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/evaluate.py
```

Run `python scripts/benchmark.py` locally when installation, validation, or
evaluation performance changes. Never make benchmark timing a CI gate.
