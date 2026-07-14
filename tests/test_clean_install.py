import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.clean_install import (
    REQUIRED_COMMANDS,
    format_clean_install_proof,
    load_clean_install_proof,
    sanitize_result,
    summarize_clean_install_proof,
    write_clean_install_proof,
)
from engine.project_paths import find_project_root, looks_like_project_root
from engine.taxonomy import load_taxonomy


ROOT = Path(__file__).resolve().parents[1]


class ProjectPathTests(unittest.TestCase):
    def test_find_project_root_finds_checkout_from_nested_path(self):
        nested = ROOT / "scripts"

        self.assertTrue(looks_like_project_root(ROOT))
        self.assertEqual(find_project_root(nested), ROOT)

    def test_taxonomy_loader_uses_active_project_root(self):
        countries = load_taxonomy("countries")

        self.assertIn("AU", {country["id"] for country in countries})


class CleanInstallProofTests(unittest.TestCase):
    def test_clean_install_proof_summary_requires_all_commands(self):
        proof = {
            "proof_type": "riskshard_clean_install_proof",
            "status": "pass",
            "generated_at": "2026-07-14T00:00:00+00:00",
            "summary": {"passed": len(REQUIRED_COMMANDS), "total": len(REQUIRED_COMMANDS)},
            "commands": [
                {"name": name, "returncode": 0, "command": [name], "stdout": "", "stderr": ""}
                for name in REQUIRED_COMMANDS
            ],
        }
        summary = summarize_clean_install_proof(proof)
        output = format_clean_install_proof(proof)

        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["missing_commands"], [])
        self.assertIn("RiskShard clean-install proof", output)

    def test_clean_install_proof_read_write_round_trip(self):
        proof = {
            "proof_type": "riskshard_clean_install_proof",
            "status": "pass",
            "generated_at": "2026-07-14T00:00:00+00:00",
            "summary": {"passed": 0, "total": 0},
            "commands": [],
        }

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "proof.json"
            write_clean_install_proof(proof, path)

            self.assertEqual(load_clean_install_proof(path)["proof_type"], "riskshard_clean_install_proof")

    def test_sanitize_result_replaces_local_paths(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "RiskShard"
            venv = Path(tmp) / "venv"
            result = {
                "name": "sample",
                "command": [str(venv / "bin" / "riskshard"), str(root / "scenarios")],
                "returncode": 1,
                "stdout": str(root / "sources" / "manifest.json"),
                "stderr": str(venv / "bin" / "python"),
            }

            sanitized = sanitize_result(result, root, venv)

        joined = " ".join(sanitized["command"] + [sanitized["stdout"], sanitized["stderr"]])
        self.assertIn("$RISKSHARD_ROOT", joined)
        self.assertIn("$RISKSHARD_VENV", joined)
        self.assertNotIn(str(root), joined)
        self.assertNotIn(str(venv), joined)


if __name__ == "__main__":
    unittest.main()
