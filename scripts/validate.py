#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "skills" / "engineering-agent-hierarchy" / "SKILL.md"
REQUIRED = [
    CANON,
    ROOT / ".agents" / "skills" / "engineering-agent-hierarchy" / "SKILL.md",
    ROOT / ".claude" / "skills" / "engineering-agent-hierarchy" / "SKILL.md",
    ROOT / "skills" / "engineering-agent-hierarchy" / "references" / "reasoning-depth-and-routing.md",
    ROOT / "skills" / "engineering-agent-hierarchy" / "references" / "delegation-and-escalation-protocol.md",
    ROOT / "skills" / "engineering-agent-hierarchy" / "references" / "work-packet-template.md",
    ROOT / "skills" / "engineering-agent-hierarchy" / "references" / "review-and-integration-protocol.md",
    ROOT / "skills" / "engineering-agent-hierarchy" / "references" / "development-execution-contract.md",
]

errors = []
for path in REQUIRED:
    if not path.is_file():
        errors.append(f"missing: {path.relative_to(ROOT)}")

for path in [p for p in REQUIRED if p.name == "SKILL.md" and p.is_file()]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"frontmatter missing: {path.relative_to(ROOT)}")
        continue
    head = text.split("---", 2)[1]
    if not re.search(r"^name:\s*engineering-agent-hierarchy\s*$", head, re.M):
        errors.append(f"name mismatch: {path.relative_to(ROOT)}")
    if not re.search(r"^description:\s*\S", head, re.M):
        errors.append(f"description missing: {path.relative_to(ROOT)}")

contract = REQUIRED[-1]
if contract.is_file():
    c = contract.read_text(encoding="utf-8")
    for marker in [
        "Development Execution Contract",
        "GitHub PR Review Inbox",
        "Mandatory code review",
        "Definition of Done",
    ]:
        if marker not in c:
            errors.append(f"execution contract missing marker: {marker}")

for entry in REQUIRED[1:3]:
    if entry.is_file() and "skills/engineering-agent-hierarchy/SKILL.md" not in entry.read_text(encoding="utf-8"):
        errors.append(f"provider entrypoint does not reference canonical skill: {entry.relative_to(ROOT)}")

if errors:
    print("FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("OK: engineering-agent-hierarchy skill structure is valid")
