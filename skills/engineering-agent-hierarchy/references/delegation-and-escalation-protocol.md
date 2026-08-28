# Delegation and Escalation Protocol

## 1. HIGH prepares the work

Before delegation, HIGH determines:

- Goal
- Context
- Constraints
- Done when
- Non-goals
- Risk class
- Reasoning depth
- Current increment
- Directly affected files/call paths/data flow
- External decisions or approvals
- Minimum useful validation

If a high-reasoning decision is unresolved, do not push that ambiguity into a LOW work packet.

## 2. HIGH creates a bounded work packet

Each write-enabled LOW agent gets explicit ownership. Include:

- one objective;
- allowed files/area;
- prohibited scope;
- invariants and guardrails;
- acceptance criteria;
- expected tests/evidence;
- escalation triggers;
- output format.

Parallel writers must not overlap files, migrations, public contracts, or core logic.

## 3. LOW investigates before editing

LOW reads only the focused scope needed to understand the packet. It should identify contradictions early rather than implement blindly.

LOW may make safe local implementation decisions that do not alter packet invariants.

LOW may not silently reinterpret a public requirement, trust boundary, contract, or irreversible behavior.

## 4. LOW executes

Preferred sequence:

1. reproduce/verify current behavior where useful;
2. implement the smallest sufficient change;
3. add or update focused regression evidence;
4. run targeted validation;
5. inspect its own diff for accidental scope expansion;
6. return concise evidence.

## 5. Escalation triggers

Escalate immediately for:

- auth/authz/isolation or sensitive-data behavior not already specified;
- schema/public API/cross-service contract changes not already specified;
- migration-history/destructive-data implications;
- concurrency/retry/idempotency/transaction ambiguity;
- production/destructive/irreversible operation;
- hidden dependency that invalidates the packet;
- file/core-logic ownership collision;
- repeated failures indicating the assumed solution may be wrong;
- evidence contradicting an invariant;
- inability to obtain required validation without broadening scope materially.

## 6. LOW escalation format

Return exactly the engineering information HIGH needs:

- **Observation:** what was discovered.
- **Evidence:** file/line/test/log/result.
- **Why current packet is insufficient:** which guardrail/assumption is affected.
- **Decision needed:** one sentence.
- **Safe options:** preferably 2–3 with trade-offs.
- **Unaffected work:** anything that can still proceed independently.

Do not dump private chain-of-thought. Report conclusions and evidence.

## 7. HIGH resolves

HIGH chooses one of:

- clarify the invariant and return the same packet;
- narrow or split the packet;
- upgrade the work to HIGH ownership;
- assign a specialist/reviewer;
- classify the increment as `BLOCKED_DECISION`, `BLOCKED_EXTERNAL_APPROVAL`, or `BLOCKED_ENVIRONMENT` according to the execution contract;
- defer unrelated work and continue with another independent increment.

## 8. Evidence return

LOW completion report:

- files changed;
- behavior changed;
- tests/commands executed with result;
- evidence for acceptance criteria;
- assumptions made inside permitted guardrails;
- unresolved questions/risks;
- newly discovered out-of-scope issues.

"Done" without evidence is not a valid worker result.
