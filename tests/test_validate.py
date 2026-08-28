from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate


class ValidationUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(
            prefix="senior-says-validate-test-"
        )
        self.addCleanup(self.tempdir.cleanup)
        self.temp_root = Path(self.tempdir.name)

    def copy_skill(self) -> Path:
        source = validate.ROOT / "skills" / validate.SKILL_NAME
        destination = self.temp_root / validate.SKILL_NAME
        shutil.copytree(source, destination)
        return destination

    def copy_repository(self) -> Path:
        destination = self.temp_root / "repo"
        shutil.copytree(
            validate.ROOT,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                "__pycache__",
                ".pytest_cache",
                "artifacts",
            ),
        )
        return destination

    def test_current_repository_is_valid(self) -> None:
        self.assertEqual(validate.validate_repository(), [])

    def test_installed_skill_tree_is_valid(self) -> None:
        skill = self.copy_skill()
        self.assertEqual(validate.validate_skill_tree(skill), [])

    def test_missing_reference_is_reported(self) -> None:
        skill = self.copy_skill()
        (skill / "references" / "work-packet-template.md").unlink()

        errors = validate.validate_skill_tree(skill)

        self.assertTrue(any("work-packet-template.md" in error for error in errors))

    def test_bad_frontmatter_name_is_reported(self) -> None:
        skill = self.copy_skill()
        skill_file = skill / "SKILL.md"
        skill_file.write_text(
            skill_file.read_text(encoding="utf-8").replace(
                "name: engineering-agent-hierarchy",
                "name: wrong-name",
                1,
            ),
            encoding="utf-8",
        )

        errors = validate.validate_skill_tree(skill)

        self.assertIn("name mismatch: SKILL.md", errors)

    def test_provider_entrypoint_must_reference_canonical_skill(self) -> None:
        repository = self.copy_repository()
        entrypoint = (
            repository
            / ".agents"
            / "skills"
            / validate.SKILL_NAME
            / "SKILL.md"
        )
        entrypoint.write_text(
            "---\n"
            "name: engineering-agent-hierarchy\n"
            "description: test\n"
            "---\n"
            "No canonical reference.\n",
            encoding="utf-8",
        )

        errors = validate.validate_repository(repository)

        self.assertTrue(
            any(
                "provider entrypoint does not reference canonical skill" in error
                for error in errors
            )
        )

    def test_codex_plugin_manifest_must_point_to_skills(self) -> None:
        repository = self.copy_repository()
        manifest = repository / ".codex-plugin" / "plugin.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["skills"] = "../outside"
        manifest.write_text(json.dumps(payload), encoding="utf-8")

        errors = validate.validate_repository(repository)

        self.assertIn(
            "Codex plugin manifest skills must point to ./skills/",
            errors,
        )

    def test_corpus_expected_result_must_match_policy(self) -> None:
        repository = self.copy_repository()
        scenarios_path = repository / "evaluation" / "scenarios.json"
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
        scenarios[0]["expected"] = {
            "decision": "HIGH_OWNS",
            "must_escalate": True,
        }
        scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")

        errors = validate.validate_repository(repository)

        self.assertTrue(
            any("docs-typo expected HIGH_OWNS" in error for error in errors)
        )

    def test_ci_must_not_run_benchmark(self) -> None:
        repository = self.copy_repository()
        workflow = repository / ".github" / "workflows" / "ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8")
            + "\n      - run: python scripts/benchmark.py\n",
            encoding="utf-8",
        )

        errors = validate.validate_repository(repository)

        self.assertIn("CI must not run local performance benchmarks", errors)

    def test_ci_must_not_run_installation_smoke_test(self) -> None:
        repository = self.copy_repository()
        workflow = repository / ".github" / "workflows" / "ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8")
            + "\n      - run: python scripts/smoke_test.py\n",
            encoding="utf-8",
        )

        errors = validate.validate_repository(repository)

        self.assertIn(
            "CI must keep installation smoke tests as explicit local checks",
            errors,
        )

    def test_ci_actions_must_use_full_commit_shas(self) -> None:
        repository = self.copy_repository()
        workflow = repository / ".github" / "workflows" / "ci.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
                "actions/checkout@v6",
            ),
            encoding="utf-8",
        )
        errors = validate.validate_repository(repository)
        self.assertTrue(
            any(
                "CI actions must be pinned to a full commit SHA" in error
                for error in errors
            )
        )

    def test_cli_validates_an_installed_skill(self) -> None:
        skill = self.copy_skill()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = validate.main(["--skill-root", str(skill)])

        self.assertEqual(exit_code, 0)
        self.assertIn("structure is valid", output.getvalue())


if __name__ == "__main__":
    unittest.main()
