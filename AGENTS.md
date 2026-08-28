# Repository Instructions

This repository contains the canonical `engineering-agent-hierarchy` skill.

When modifying it:

1. Keep `skills/engineering-agent-hierarchy/SKILL.md` provider-neutral.
2. Keep Codex-specific behavior in `.agents/` or `examples/codex/`.
3. Keep Claude-specific behavior in `.claude/` or `examples/claude/`.
4. Do not duplicate the full canonical skill into provider entrypoints.
5. Preserve the user's `development-execution-contract.md` as the authoritative delivery/review contract unless explicitly asked to revise it.
6. Run `python scripts/validate.py` after structural edits.
