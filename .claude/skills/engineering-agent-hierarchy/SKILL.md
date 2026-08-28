---
name: engineering-agent-hierarchy
description: Coordinate high-reasoning and lower-cost software-engineering agents using risk/reasoning-based routing, bounded work packets, escalation, independent review, and delivery gates. Use for multi-agent coding, subagent delegation, or senior/junior-style AI engineering workflows.
---

# Claude Code entrypoint

This repository keeps one canonical cross-provider skill.

Read and follow:

`skills/engineering-agent-hierarchy/SKILL.md`

Resolve its referenced files relative to:

`skills/engineering-agent-hierarchy/`

Claude-specific note: map semantic roles to the available model tiers. Prefer an Opus-class model for `HIGH_TIER`, a Sonnet-class model for normal `LOW_TIER` coding work, and reserve Haiku-class execution for truly mechanical/read-only work unless the user explicitly chooses otherwise.
