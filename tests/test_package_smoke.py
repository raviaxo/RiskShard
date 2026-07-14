import unittest
from pathlib import Path

from engine.package_smoke import (
    build_package_smoke_report,
    format_package_smoke_report,
    parse_project_script_targets,
    parse_project_scripts,
)


ROOT = Path(__file__).resolve().parents[1]


class PackageSmokeTests(unittest.TestCase):
    def test_package_smoke_imports_declared_entry_points(self):
        report = build_package_smoke_report(ROOT)
        output = format_package_smoke_report(report)
        by_name = {item["name"]: item for item in report["entry_points"]}

        self.assertEqual(report["status"], "pass")
        self.assertEqual(by_name["riskshard-benchmark"]["status"], "pass")
        self.assertEqual(by_name["riskshard-beta"]["status"], "pass")
        self.assertEqual(by_name["riskshard-clean-install"]["status"], "pass")
        self.assertEqual(by_name["riskshard-toprisks"]["status"], "pass")
        self.assertEqual(by_name["riskshard-package-smoke"]["status"], "pass")
        self.assertIn("RiskShard package smoke", output)
        self.assertIn("importable callable", output)

    def test_parse_project_script_targets_reads_names_and_targets(self):
        text = """
[project.scripts]
riskshard = "scripts.fair_calc:main"
riskshard-doctor = "scripts.riskshard_doctor:main"

[tool.setuptools]
packages = ["engine"]
"""

        self.assertEqual(
            parse_project_script_targets(text),
            {
                "riskshard": "scripts.fair_calc:main",
                "riskshard-doctor": "scripts.riskshard_doctor:main",
            },
        )
        self.assertEqual(parse_project_scripts(text), ["riskshard", "riskshard-doctor"])


if __name__ == "__main__":
    unittest.main()
