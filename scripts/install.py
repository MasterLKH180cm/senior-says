#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "engineering-agent-hierarchy"
NAME = "engineering-agent-hierarchy"


def install(dest: Path, force: bool) -> None:
    if dest.exists():
        if not force:
            raise SystemExit(f"Refusing to overwrite existing skill: {dest}\nUse --force to replace it.")
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, dest)
    print(f"Installed: {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the engineering-agent-hierarchy skill for Codex and/or Claude Code.")
    parser.add_argument("provider", choices=["codex", "claude", "both"])
    parser.add_argument("--force", action="store_true", help="Replace an existing installed copy.")
    args = parser.parse_args()

    home = Path.home()
    if args.provider in {"codex", "both"}:
        install(home / ".agents" / "skills" / NAME, args.force)
    if args.provider in {"claude", "both"}:
        install(home / ".claude" / "skills" / NAME, args.force)


if __name__ == "__main__":
    main()
