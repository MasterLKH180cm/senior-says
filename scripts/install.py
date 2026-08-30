#!/usr/bin/env python3
"""Safely install the canonical skill into Codex and/or Claude user roots."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "engineering-agent-hierarchy"
NAME = "engineering-agent-hierarchy"
PROVIDERS = ("codex", "claude", "both")
PROVIDER_ROOTS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
}


class InstallationError(RuntimeError):
    """Raised when an installation cannot be completed or rolled back safely."""


# Compatibility alias retained for callers from the initial repository version.
InstallError = InstallationError


def path_exists(path: Path) -> bool:
    """Return True for files, directories, and broken symlinks."""

    return os.path.lexists(path)


def remove_path(path: Path) -> None:
    """Remove a file, symlink, or directory without following symlinks."""

    if not path_exists(path):
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def rename_path(source: Path, destination: Path) -> None:
    """Rename a path on the same filesystem; kept injectable for rollback tests."""

    source.rename(destination)


def provider_destinations(provider: str, home: Path) -> tuple[Path, ...]:
    """Resolve fixed provider destinations below an explicit home directory."""

    if provider == "both":
        providers = ("codex", "claude")
    elif provider in PROVIDER_ROOTS:
        providers = (provider,)
    else:
        raise ValueError(f"unsupported provider: {provider}")

    expanded_home = Path(home).expanduser()
    return tuple(expanded_home / PROVIDER_ROOTS[item] / NAME for item in providers)


def validate_source(source: Path) -> None:
    """Reject incomplete or unsafe source trees before mutating destinations."""

    if source.is_symlink():
        raise InstallationError(f"Skill source must not be a symlink: {source}")
    if not source.is_dir():
        raise InstallationError(f"Skill source does not exist: {source}")
    if not (source / "SKILL.md").is_file():
        raise InstallationError(f"Skill source is missing SKILL.md: {source}")
    if not (source / "references").is_dir():
        raise InstallationError(f"Skill source is missing references/: {source}")

    symlinks = [path for path in source.rglob("*") if path.is_symlink()]
    if symlinks:
        rendered = ", ".join(str(path.relative_to(source)) for path in symlinks)
        raise InstallationError(f"Skill source contains symlink(s): {rendered}")


def _resolved(path: Path) -> Path:
    return path.resolve(strict=False)


def _paths_overlap(first: Path, second: Path) -> bool:
    first_resolved = _resolved(first)
    second_resolved = _resolved(second)
    return (
        first_resolved == second_resolved
        or first_resolved in second_resolved.parents
        or second_resolved in first_resolved.parents
    )


def preflight(
    source: Path,
    destinations: Iterable[Path],
    *,
    force: bool,
) -> tuple[Path, ...]:
    """Validate every destination before any installation write occurs."""

    targets = tuple(Path(destination).expanduser().absolute() for destination in destinations)
    if not targets:
        raise InstallationError("At least one installation destination is required.")

    normalized = [os.path.normcase(str(_resolved(target))) for target in targets]
    if len(set(normalized)) != len(normalized):
        raise InstallationError("Duplicate installation destinations are not allowed.")

    for destination in targets:
        if _paths_overlap(source, destination):
            raise InstallationError(
                f"Skill source and destination must not overlap: {source} <-> {destination}"
            )
        if destination.is_symlink():
            raise InstallationError(
                f"Refusing to replace symlink destination: {destination}"
            )
        if path_exists(destination) and not destination.is_dir():
            raise InstallationError(
                f"Installation destination is not a directory: {destination}"
            )
        if destination.exists() and not force:
            raise InstallationError(
                f"Refusing to overwrite existing skill: {destination}\n"
                "Use --force to replace it."
            )
        if path_exists(destination.parent) and not destination.parent.is_dir():
            raise InstallationError(
                f"Installation parent is not a directory: {destination.parent}"
            )

    for first, second in combinations(targets, 2):
        if _paths_overlap(first, second):
            raise InstallationError(
                f"Installation destinations must not overlap: {first} <-> {second}"
            )

    return targets


def _reserve_sibling(parent: Path, prefix: str) -> Path:
    """Return a unique, currently absent path on the destination filesystem."""

    reserved = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
    reserved.rmdir()
    return reserved


def _cleanup_paths(paths: Iterable[Path], errors: list[str], action: str) -> None:
    for path in paths:
        if not path_exists(path):
            continue
        try:
            remove_path(path)
        except OSError as exc:
            errors.append(f"{action} {path}: {exc}")


def install_many(
    source: Path,
    destinations: Sequence[Path],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[Path, ...]:
    """Install one source into all destinations using staging and rollback.

    Every destination is preflighted before mutation. All copies are staged beside
    their final destinations, then committed by same-filesystem rename. If a later
    destination fails, earlier writes are removed and previous installs restored.
    """

    source = Path(source).expanduser().absolute()
    validate_source(source)
    targets = preflight(source, destinations, force=force)
    if dry_run:
        return targets

    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    committed: list[Path] = []

    try:
        # Stage every provider copy before changing any existing installation.
        for destination in targets:
            destination.parent.mkdir(parents=True, exist_ok=True)
            stage = _reserve_sibling(destination.parent, f".{NAME}.stage-")
            # Register before copytree so a partially-created copy is cleaned.
            staged[destination] = stage
            shutil.copytree(source, stage)

        for destination in targets:
            # Recheck after staging so a newly-created path follows the same policy.
            if destination.is_symlink():
                raise InstallationError(
                    f"Refusing to replace symlink destination: {destination}"
                )
            if path_exists(destination):
                if not destination.is_dir():
                    raise InstallationError(
                        f"Installation destination is not a directory: {destination}"
                    )
                if not force:
                    raise InstallationError(
                        f"Installation destination appeared during install: {destination}"
                    )
                backup = _reserve_sibling(destination.parent, f".{NAME}.backup-")
                rename_path(destination, backup)
                backups[destination] = backup

            rename_path(staged[destination], destination)
            committed.append(destination)

    except Exception as exc:
        rollback_errors: list[str] = []

        _cleanup_paths(
            reversed(committed),
            rollback_errors,
            "remove new installation",
        )

        for destination in reversed(targets):
            backup = backups.get(destination)
            if backup is None or not path_exists(backup):
                continue
            try:
                if path_exists(destination):
                    remove_path(destination)
                rename_path(backup, destination)
            except OSError as rollback_exc:
                rollback_errors.append(
                    f"restore previous installation {destination} from {backup}: "
                    f"{rollback_exc}"
                )

        _cleanup_paths(staged.values(), rollback_errors, "remove staged copy")

        if rollback_errors:
            detail = "; ".join(rollback_errors)
            raise InstallationError(
                f"Unable to install skill and rollback was incomplete: {exc}; {detail}"
            ) from exc
        if isinstance(exc, InstallationError):
            raise
        raise InstallationError(f"Unable to install skill: {exc}") from exc

    cleanup_errors: list[str] = []
    _cleanup_paths(staged.values(), cleanup_errors, "remove staged copy")
    _cleanup_paths(backups.values(), cleanup_errors, "remove backup")
    if cleanup_errors:
        raise InstallationError(
            "Skill was installed, but temporary cleanup failed: "
            + "; ".join(cleanup_errors)
        )

    return targets


def install(
    destination: Path,
    force: bool = False,
    source: Path = SOURCE,
) -> Path:
    """Install one destination; retained as a small public convenience wrapper."""

    return install_many(source, (destination,), force=force)[0]


def install_provider(
    provider: str,
    *,
    home: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
    source: Path = SOURCE,
) -> tuple[Path, ...]:
    """Install one or both provider copies below an explicit or current home."""

    resolved_home = (home or Path.home()).expanduser()
    destinations = provider_destinations(provider, resolved_home)
    return install_many(source, destinations, force=force, dry_run=dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Install the engineering-agent-hierarchy skill for Codex and/or "
            "Claude Code."
        )
    )
    parser.add_argument("provider", choices=PROVIDERS)
    parser.add_argument(
        "--home",
        type=Path,
        help="Install below this home directory instead of the current user's home.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing copies after staging every requested provider install.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print destinations without changing files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        destinations = install_provider(
            args.provider,
            home=args.home,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (InstallationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    verb = "Would install" if args.dry_run else "Installed"
    for destination in destinations:
        print(f"{verb}: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
