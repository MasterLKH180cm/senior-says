# Review and Integration Protocol

## HIGH integrates evidence, not summaries alone

After a worker reports completion:

1. inspect the actual changed files/diff;
2. verify the packet stayed in scope;
3. check the worker's validation evidence;
4. reconcile cross-worker assumptions;
5. verify system-level invariants that LOW was not responsible for;
6. run only additional validation required to close an evidence gap.

Do not rerun every worker test merely because integration occurred if relevant files/behavior did not change.

## Independent reviewer

Use an independent reviewer when production code changes or risk warrants it. Prefer read-only access.

Reviewer checks:

- correctness and acceptance criteria;
- regression/backward compatibility;
- edge cases/invalid states;
- error/failure propagation;
- hidden side effects/state transitions;
- concurrency/retry/idempotency when applicable;
- API/schema/config/migration drift;
- auth/permission/isolation when applicable;
- test quality and false positives;
- maintainability/scope discipline/rollback.

Reviewer returns concrete actionable findings. Avoid style-only churn.

## Bad-smell review

HIGH must ensure code-changing increments receive a final smell pass for:

- unnecessary abstraction/premature generalization;
- thin/fake helpers and needless indirection;
- duplication or inconsistent parallel logic;
- dead/debug/temporary code;
- brittle or implementation-coupled tests;
- swallowed errors/silent fallback;
- hidden mutable/shared state;
- excessive coupling/mixed responsibilities;
- unrelated refactor/format noise;
- contract/auth/migration drift;
- insecure defaults or sensitive logging.

Classify real findings as:

- `Fixed in this PR`
- `Found but not fixed`
- `Newly introduced risk`

Do not fabricate findings to make the report look complete.

## Focused security review

For production diffs, HIGH checks at least:

- secrets/sensitive-data leakage;
- attacker-controlled input and validation/escaping;
- auth/permission/isolation regressions;
- fail-open defaults;
- filesystem/network side effects;
- config/dependency/feature-flag/disabled-route risk.

Use one specialist security workflow only when the actual trust boundary/risk warrants it.

## Git/PR ownership

HIGH owns final Git truth:

- branch safety;
- staged-diff hygiene;
- commit/push claims;
- PR body and scope;
- latest review comments/threads/checks at required checkpoints;
- blocking feedback classification and follow-up;
- truthful `CI pending` / `Pending external approval` status;
- no automatic merge unless explicitly requested and all gates are satisfied.
