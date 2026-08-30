# Repository Instructions

Use the canonical skill at `skills/engineering-agent-hierarchy/SKILL.md`.
Provider-specific wrappers must remain thin; do not fork the workflow into
separate Claude and Codex copies. Preserve
`references/development-execution-contract.md` as the authoritative execution
contract unless explicitly asked to revise it.

Use GitHub Flow and run the repository unit tests, validator, and deterministic
evaluation before declaring a change complete. Run the benchmark locally when
changing installation, validation, or evaluation performance paths; do not run
timing benchmarks in CI.
