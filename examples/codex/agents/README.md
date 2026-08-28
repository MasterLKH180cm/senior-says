# Codex agent-role examples

Codex model IDs and account entitlements can change. These examples intentionally avoid an active hard-coded model ID.

Create local/user/project agent-role TOML files using the current Codex configuration schema, then map:

- `senior_orchestrator` → strongest supported model, `high`/`xhigh` reasoning.
- `junior_executor` → cheaper coding-capable model, `low`/`medium` reasoning.
- `independent_reviewer` → strong model, read-only sandbox where supported.

Do not paste placeholder model IDs into active configuration without replacing them with a model that your Codex environment supports.
