#!/usr/bin/env python3
"""Run an isolated local install smoke test without touching the real home."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.install import InstallError, install_provider  # noqa: E402
from scripts.validate import validate_skill_tree  # noqa: E402


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def run_smoke(home: Path) -> list[str]:
    """Exercise dry-run, dual install, overwrite protection, and replacement."""

    observations: list[str] = []

    planned = install_provider("both", home=home, dry_run=True)
    if any(destination.exists() for destination in planned):
        raise RuntimeError("dry-run unexpectedly created an installation")
    observations.append("dry-run completed without filesystem mutation")

    destinations = install_provider("both", home=home)
    for destination in destinations:
        errors = validate_skill_tree(destination)
        if errors:
            raise RuntimeError(f"invalid installed skill at {destination}: {errors}")
        observations.append(f"validated {destination}")

    codex, claude = destinations
    if tree_digest(codex) != tree_digest(claude):
        raise RuntimeError("Codex and Claude installed trees differ")
    observations.append("provider installs are byte-identical")

    try:
        install_provider("codex", home=home)
    except InstallError:
        observations.append("overwrite protection refused a second install")
    else:
        raise RuntimeError("second install unexpectedly overwrote the Codex copy")

    sentinel = codex / "stale-local-file.txt"
    sentinel.write_text("remove me", encoding="utf-8")
    install_provider("codex", home=home, force=True)
    if sentinel.exists():
        raise RuntimeError("force install did not replace the stale copy")
    errors = validate_skill_tree(codex)
    if errors:
        raise RuntimeError(f"force-installed Codex skill is invalid: {errors}")
    observations.append("force install replaced the stale copy and remained valid")

    return observations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        type=Path,
        help=(
            "Use this disposable home. When omitted, a temporary directory is "
            "created and removed."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.home:
            args.home.mkdir(parents=True, exist_ok=True)
            observations = run_smoke(args.home)
            label = str(args.home)
        else:
            with tempfile.TemporaryDirectory(prefix="senior-says-smoke-") as temp:
                observations = run_smoke(Path(temp))
            label = "temporary home (removed)"
        print(f"SMOKE PASS: {label}")
        for observation in observations:
            print(f"- {observation}")
        return 0
    except (InstallError, OSError, RuntimeError) as exc:
        print(f"SMOKE FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
