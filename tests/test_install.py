from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import install


class InstallUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="senior-says-install-test-")
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.home = self.root / "home"

    def hidden_install_artifacts(self) -> list[Path]:
        if not self.home.exists():
            return []
        return [
            path
            for path in self.home.rglob(f".{install.NAME}.*")
            if path.exists()
            and path.name.startswith(
                (
                    f".{install.NAME}.stage-",
                    f".{install.NAME}.backup-",
                )
            )
        ]

    def test_provider_destinations_are_fixed_below_home(self) -> None:
        self.assertEqual(
            install.provider_destinations("both", self.home),
            (
                self.home / ".agents" / "skills" / install.NAME,
                self.home / ".claude" / "skills" / install.NAME,
            ),
        )

    def test_invalid_provider_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported provider"):
            install.provider_destinations("unknown", self.home)

    def test_installs_both_provider_copies(self) -> None:
        destinations = install.install_provider("both", home=self.home)

        self.assertEqual(len(destinations), 2)
        for destination in destinations:
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue(
                (
                    destination
                    / "references"
                    / "development-execution-contract.md"
                ).is_file()
            )
        self.assertEqual(self.hidden_install_artifacts(), [])

    def test_refuses_to_overwrite_without_force(self) -> None:
        (destination,) = install.install_provider("codex", home=self.home)

        with self.assertRaisesRegex(install.InstallError, "Refusing to overwrite"):
            install.install_provider("codex", home=self.home)

        self.assertTrue((destination / "SKILL.md").is_file())

    def test_force_replaces_the_entire_existing_copy(self) -> None:
        (destination,) = install.install_provider("codex", home=self.home)
        stale = destination / "stale.txt"
        stale.write_text("stale", encoding="utf-8")

        install.install_provider("codex", home=self.home, force=True)

        self.assertFalse(stale.exists())
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertEqual(self.hidden_install_artifacts(), [])

    def test_partial_copy_failure_preserves_existing_destination(self) -> None:
        (destination,) = install.install_provider("codex", home=self.home)
        sentinel = destination / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")

        def partial_copy(_source: Path, target: Path) -> None:
            Path(target).mkdir(parents=True)
            (Path(target) / "partial.txt").write_text("partial", encoding="utf-8")
            raise OSError("simulated copy failure")

        with mock.patch("scripts.install.shutil.copytree", side_effect=partial_copy):
            with self.assertRaisesRegex(install.InstallError, "Unable to install skill"):
                install.install_provider("codex", home=self.home, force=True)

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertEqual(self.hidden_install_artifacts(), [])

    def test_second_provider_commit_failure_rolls_back_both_previous_copies(self) -> None:
        codex, claude = install.install_provider("both", home=self.home)
        codex_sentinel = codex / "codex-sentinel.txt"
        claude_sentinel = claude / "claude-sentinel.txt"
        codex_sentinel.write_text("codex-old", encoding="utf-8")
        claude_sentinel.write_text("claude-old", encoding="utf-8")
        original_rename = install.rename_path

        def fail_second_stage(source: Path, destination: Path) -> None:
            if source.name.startswith(f".{install.NAME}.stage-") and destination == claude:
                raise OSError("simulated second-provider commit failure")
            original_rename(source, destination)

        with mock.patch("scripts.install.rename_path", side_effect=fail_second_stage):
            with self.assertRaisesRegex(install.InstallError, "Unable to install skill"):
                install.install_provider("both", home=self.home, force=True)

        self.assertEqual(codex_sentinel.read_text(encoding="utf-8"), "codex-old")
        self.assertEqual(claude_sentinel.read_text(encoding="utf-8"), "claude-old")
        self.assertEqual(self.hidden_install_artifacts(), [])

    def test_missing_source_is_rejected(self) -> None:
        destination = self.home / ".agents" / "skills" / install.NAME
        with self.assertRaisesRegex(install.InstallError, "source does not exist"):
            install.install(destination, source=self.root / "missing")

    def test_symlink_inside_source_is_rejected(self) -> None:
        source = self.root / "source"
        (source / "references").mkdir(parents=True)
        (source / "SKILL.md").write_text("skill", encoding="utf-8")
        target = self.root / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        try:
            (source / "references" / "linked.txt").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable in this environment")

        destination = self.home / ".agents" / "skills" / install.NAME
        with self.assertRaisesRegex(install.InstallError, "contains symlink"):
            install.install(destination, source=source)

    def test_source_and_destination_must_not_overlap(self) -> None:
        destination = install.SOURCE / ".agents" / "skills" / install.NAME
        with self.assertRaisesRegex(install.InstallError, "must not overlap"):
            install.install(destination)

    def test_duplicate_destinations_are_rejected(self) -> None:
        destination = self.home / ".agents" / "skills" / install.NAME
        with self.assertRaisesRegex(install.InstallError, "Duplicate"):
            install.install_many(install.SOURCE, (destination, destination))

    def test_symlink_destination_is_rejected(self) -> None:
        real_destination = self.root / "real-destination"
        real_destination.mkdir()
        destination = self.home / ".agents" / "skills" / install.NAME
        destination.parent.mkdir(parents=True)
        try:
            destination.symlink_to(real_destination, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable in this environment")

        with self.assertRaisesRegex(install.InstallError, "symlink destination"):
            install.install(destination)

        self.assertTrue(real_destination.is_dir())

    def test_dry_run_does_not_create_destinations(self) -> None:
        destinations = install.install_provider("both", home=self.home, dry_run=True)
        self.assertTrue(all(not destination.exists() for destination in destinations))
        self.assertFalse(self.home.exists())

    def test_cli_supports_explicit_sandbox_home(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = install.main(["both", "--home", str(self.home)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Installed:", output.getvalue())
        self.assertTrue(
            (self.home / ".agents" / "skills" / install.NAME / "SKILL.md").is_file()
        )
        self.assertTrue(
            (self.home / ".claude" / "skills" / install.NAME / "SKILL.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
