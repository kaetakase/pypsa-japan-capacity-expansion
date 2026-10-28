"""Offline regression tests for scenario configuration and file staging.

Tests do not execute PyPSA or prove agreement with manuscript results.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_scenarios.py"
MATRIX = ROOT / "scenarios" / "scenario_matrix.csv"
INPUT = ROOT / "input"


class ScenarioStagingTests(unittest.TestCase):
    def test_matrix_and_generated_policy(self):
        expected = {
            "WG": (False, False),
            "REI": (False, False),
            "WG-CO2": (True, False),
            "REI-CO2": (True, False),
            "WG-SEP": (True, True),
            "REI-SEP": (True, True),
        }
        with MATRIX.open(newline="", encoding="utf-8") as f:
            conf = {row["case"]: row for row in csv.DictReader(f)}
        self.assertEqual(set(conf), set(expected))
        raw_policy_hash = hashlib.sha256((INPUT / "policy_2040.csv").read_bytes()).hexdigest()
        raw_cost_hash = hashlib.sha256((INPUT / "technology_cost_2040.csv").read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as work:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--all", "--time-mode", "rep4", "--dry-run", "--output-root", work],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            for case, (co2, mix) in expected.items():
                out = Path(work) / "rep4" / case.lower()
                with (out / "input" / "policy_2040.csv").open(newline="", encoding="utf-8") as f:
                    policy = {r["parameter"]: r["value"] for r in csv.DictReader(f)}
                self.assertEqual(policy["use_co2_intensity_constraint"] == "True", co2)
                self.assertEqual(policy["use_basic_mix_constraint"] == "True", mix)
                self.assertEqual("co2_intensity_tco2_per_mwh" in policy, co2)
                if co2:
                    self.assertEqual(float(policy["co2_intensity_tco2_per_mwh"]), 0.04)
                self.assertEqual(int(policy["carbon_price"]), 0)
                self.assertEqual(("basic_mix_file" in policy), mix)
                source = INPUT / conf[case]["cost_input"]
                self.assertEqual((out / "input" / "technology_cost_2040.csv").read_bytes(), source.read_bytes())
                manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["case"], case)
                self.assertEqual(manifest["time_mode"], "rep4")
                self.assertEqual(manifest["source_cost_input"], conf[case]["cost_input"])
                self.assertEqual(manifest["reproducibility_status"], "staged_only; optimization not yet independently verified")
        self.assertEqual(hashlib.sha256((INPUT / "policy_2040.csv").read_bytes()).hexdigest(), raw_policy_hash)
        self.assertEqual(hashlib.sha256((INPUT / "technology_cost_2040.csv").read_bytes()).hexdigest(), raw_cost_hash)

    def test_reference_policy_key_is_lowercase(self):
        with (INPUT / "policy_2040_intensity.csv").open(newline="", encoding="utf-8") as f:
            policy = {r["parameter"]: r["value"] for r in csv.DictReader(f)}
        self.assertIn("co2_intensity_tco2_per_mwh", policy)
        self.assertNotIn("CO2_INTENSITY_TCO2_PER_MWH", policy)


if __name__ == "__main__":
    unittest.main()
