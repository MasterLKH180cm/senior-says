# Reasoning Depth and Routing

## Purpose

Use this reference to decide which model tier should own a unit of engineering work.

Routing uses five independent dimensions:

1. **Implementation complexity** — coding effort and technical difficulty.
2. **Reasoning depth** — how many layers of correctness/system/problem reasoning are required.
3. **Risk** — blast radius if wrong.
4. **Ambiguity** — how much of the correct behavior or boundary is undefined.
5. **Domain familiarity** — how much context the assigned agent already has about the relevant code and business behavior.

Do not collapse these into a single "difficulty" score.

## Five reasoning levels

### R1 — Implementation

Question: **How do I write this?**

Typical concerns:
- syntax and framework usage;
- API/library calls;
- localized happy-path implementation.

Default: LOW.

### R2 — Correctness

Question: **Is this actually correct?**

Typical concerns:
- validation;
- edge/boundary cases;
- error handling;
- null/empty/malformed inputs;
- regression tests.

Default: LOW if risk is bounded; HIGH review.

### R3 — Component Design

Question: **Is this a good component-level design?**

Typical concerns:
- interfaces and abstraction boundaries;
- coupling/cohesion;
- maintainability/testability;
- dependency direction.

Default: LOW may lead when domain is familiar and risk is moderate; otherwise HIGH sets design/guardrails.

### R4 — System Reasoning

Question: **What happens when this enters the whole system?**

Typical concerns:
- concurrency and race conditions;
- retries/idempotency/ordering;
- distributed failure and partial success;
- auth/authz and isolation;
- contracts, compatibility, migrations;
- observability, deployment, rollback;
- operational behavior.

Default: HIGH owns decisions. LOW receives bounded implementation.

### R5 — Problem / Organizational Reasoning

Question: **Are we solving the right problem, and can we eliminate an entire class of future problems?**

Typical concerns:
- requirement challenge/reframing;
- architecture and platform leverage;
- build vs buy;
- team/service ownership;
- long-term cognitive load;
- second/third-order effects.

Default: HIGH.

## Decision matrix

| Implementation | Reasoning | Risk | Ambiguity | Default routing |
|---|---|---|---|---|
| Low | R1–R2 | Low | Low | LOW owns; HIGH reviews |
| High/mechanical | R1–R2 | Low | Low | LOW owns, can parallelize |
| Low | R4 | High | Low/medium | HIGH decides, LOW may implement |
| Medium | R3 | Medium | Medium | HIGH guardrails/checkpoint, LOW implements |
| High | R4–R5 | High | High | HIGH leads, LOW bounded subproblems |
| Any | Any | Any | Ambiguity changes security/public behavior | HIGH or BLOCKED_DECISION |

## Important anti-patterns

### Lines-of-code routing

A tiny code change can be high-risk. Examples: authorization predicate, transaction boundary, state transition, migration default, retry policy.

### Workload routing

A very large change can still be low-reasoning if it is mechanical and well specified. Examples: repetitive test additions, generated mappings, simple client migration, deterministic rename.

### Senior-model implementation monopoly

Do not route every nontrivial coding task to HIGH. That creates a reasoning bottleneck and wastes expensive context.

### Cheap-model autonomy on ambiguous scope

Do not allow LOW to infer security semantics, contract decisions, or destructive migration behavior merely to keep moving.
