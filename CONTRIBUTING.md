# Contributing

This repository uses GitHub Flow against the default `master` branch.

## Workflow

1. Start from the latest `master`.
2. Create a short-lived branch such as `feat/*`, `fix/*`, `test/*`, or `docs/*`.
3. Keep each increment independently reviewable and reversible.
4. Run focused local validation before committing.
5. Review the final diff for correctness, bad smells, and filesystem/security
   side effects.
6. Push the branch and open a pull request to `master`.
7. Address blocking review feedback in one logical follow-up commit per review round.
8. Merge only after required CI and review gates pass.

Do not commit local homes, installed skill copies, benchmark outputs, credentials,
or temporary artifacts.

## Required local checks

Unit tests are the primary automated test layer:

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/evaluate.py
```

## Local-only acceptance checks

Run the isolated installation smoke test when installer, packaging, or provider
entrypoints change:

```bash
python scripts/smoke_test.py
python scripts/trial.py one-line-auth-change
```

Run the benchmark locally when installation, validation, or evaluation performance
changes:

```bash
python scripts/benchmark.py --iterations 50 --warmup 5 \
  --json artifacts/benchmark-local.json
```

The benchmark is intentionally excluded from CI because timing on shared runners is
noisy and not useful as a merge gate. It does not invoke Codex or Claude model
inference.
