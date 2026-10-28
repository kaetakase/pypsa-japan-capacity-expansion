#!/usr/bin/env python3
"""Stage independent, auditable PyPSA inputs for the six paper cases.

No source input files are modified. The original model executes unchanged in
an isolated run working directory containing an active `input/` folder.

Usage:
    python scripts/run_scenarios.py --list
    python scripts/run_scenarios.py --case REI-CO2 --time-mode rep4 --dry-run
    python scripts/run_scenarios.py --case REI-CO2 --time-mode full8760
    python scripts/run_scenarios.py --all --time-mode full8760

Run --dry-run first; it stages each case without importing PyPSA or solving.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input"
SCENARIO_MATRIX = ROOT / "scenarios" / "scenario_matrix.csv"
MODEL = ROOT / "pypsa_japan_capacity_expansion_2040.py"
VALID_MODES = ("rep4", "rep8", "rep10", "full8760")
REQUIRED_FIELDS = (
    "case", "cost_input", "capacity_input", "co2_intensity_active",
    "co2_intensity_tco2_per_mwh", "basic_mix_active",
    "carbon_price_jpy_per_tco2", "basic_mix_input",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parsed_bool(value: str) -> bool:
    if str(value).strip().lower() in {"true", "1", "yes"}:
        return True
    if str(value).strip().lower() in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid Boolean in scenario matrix: {value!r}")


def read_matrix() -> dict[str, dict[str, str]]:
    with SCENARIO_MATRIX.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = set(REQUIRED_FIELDS).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing scenario matrix columns: {sorted(missing)}")
        rows = list(reader)
    configs: dict[str, dict[str, str]] = {}
    for row in rows:
        case = row["case"].strip().upper()
        if not case or case in configs:
            raise ValueError(f"Empty or repeated case name: {case!r}")
        # Explicit validation before any input is written.
        parsed_bool(row["co2_intensity_active"])
        parsed_bool(row["basic_mix_active"])
        if float(row["co2_intensity_tco2_per_mwh"]) < 0:
            raise ValueError(f"Invalid CO2 intensity for {case}")
        if float(row["carbon_price_jpy_per_tco2"]) < 0:
            raise ValueError(f"Invalid carbon price for {case}")
        for key in ("cost_input", "capacity_input", "basic_mix_input"):
            name = row[key].strip()
            # Prevent accidental paths outside input/.
            if not name or Path(name).name != name or not name.endswith(".csv"):
                raise ValueError(f"Invalid input file in {case}: {key}={name!r}")
            if not (INPUT / name).is_file():
                raise FileNotFoundError(INPUT / name)
        configs[case] = row
    expected = {"WG", "REI", "WG-CO2", "REI-CO2", "WG-SEP", "REI-SEP"}
    if set(configs) != expected:
        raise ValueError(f"Scenario matrix must contain six paper cases; got {sorted(configs)}")
    return configs


def write_policy(path: Path, config: dict[str, str]) -> dict[str, str]:
    co2_on = parsed_bool(config["co2_intensity_active"])
    mix_on = parsed_bool(config["basic_mix_active"])
    # IMPORTANT: The original model AUTO-ENABLES CO2 when the key
    # 'co2_intensity_tco2_per_mwh' exists, so omit that key if CO2 is OFF.
    policy = {
        "carbon_price": config["carbon_price_jpy_per_tco2"],
        "use_co2_intensity_constraint": "True" if co2_on else "False",
        "use_basic_mix_constraint": "True" if mix_on else "False",
    }
    if co2_on:
        policy["co2_intensity_tco2_per_mwh"] = config["co2_intensity_tco2_per_mwh"]
    if mix_on:
        policy["basic_mix_file"] = "basic_mix_2040.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["parameter", "value"])
        writer.writerows(policy.items())
    return policy


def package_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0]}
    for package in ("pypsa", "linopy", "highspy", "pandas", "numpy", "xarray", "matplotlib"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not installed"
    return versions


def stage_case(config: dict[str, str], mode: str, output_root: Path, force: bool) -> Path:
    case = config["case"].strip().upper()
    workspace = output_root / mode / case.lower()
    if workspace.exists():
        if not force:
            raise FileExistsError(
                f"{workspace} already exists. Use --force to replace the prior staged run. "
                "Only do this if you do not need its previous results."
            )
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    staged_input = workspace / "input"
    shutil.copytree(INPUT, staged_input)
    staged_cost = staged_input / "technology_cost_2040.csv"
    staged_capacity = staged_input / "capacity_expansion_2040.csv"
    shutil.copy2(INPUT / config["cost_input"], staged_cost)
    shutil.copy2(INPUT / config["capacity_input"], staged_capacity)
    # Explicitly stage the same mix-definition CSV for both SEP cases.
    shutil.copy2(INPUT / config["basic_mix_input"], staged_input / "basic_mix_2040.csv")
    policy = write_policy(staged_input / "policy_2040.csv", config)
    manifest = {
        "case": case,
        "time_mode": mode,
        "source_model_sha256": sha256(MODEL),
        "source_cost_input": config["cost_input"],
        "source_capacity_input": config["capacity_input"],
        "source_basic_mix_input": config["basic_mix_input"],
        "active_policy": policy,
        "input_file_sha256": {p.name: sha256(p) for p in sorted(staged_input.glob("*.csv"))},
        "package_versions": package_versions(),
        "staged_at_utc": datetime.now(timezone.utc).isoformat(),
        "reproducibility_status": "staged_only; optimization not yet independently verified",
    }
    (workspace / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return workspace


def main() -> int:
    configs = read_matrix()
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List the six cases")
    group.add_argument("--case", choices=list(configs), help="Stage/run one case")
    group.add_argument("--all", action="store_true", help="Stage/run all six cases")
    parser.add_argument("--time-mode", choices=VALID_MODES, default="full8760")
    parser.add_argument("--dry-run", action="store_true", help="Stage and inspect inputs; do NOT run a solver")
    parser.add_argument("--force", action="store_true", help="Replace previously staged workspace and its results")
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs", help="Run workspace root")
    args = parser.parse_args()
    if args.list:
        for key, conf in configs.items():
            print(f"{key:8} cost={conf['cost_input']:29} co2={conf['co2_intensity_active']:5} mix={conf['basic_mix_active']}")
        return 0
    cases = list(configs) if args.all else [args.case]
    output_root = args.output_root.resolve()
    for case in cases:
        workspace = stage_case(configs[case], args.time_mode, output_root, args.force)
        print(f"{case}: staged at {workspace}", flush=True)
        print(f"{case}: policy at {workspace / 'input' / 'policy_2040.csv'}", flush=True)
        if args.dry_run:
            print(f"{case}: DRY RUN ONLY. No optimization performed.", flush=True)
            continue
        env = dict(os.environ)
        env.update({"CE_TIME_MODE": args.time_mode, "CE_CASE_LABEL": case.lower().replace("-", "_"), "MPLBACKEND": "Agg"})
        cmd = [sys.executable, str(MODEL)]
        print(f"{case}: executing {cmd} in {workspace}", flush=True)
        with (workspace / "execution.log").open("w", encoding="utf-8") as log:
            log.write(f"Command: {cmd}\nCase: {case}\nMode: {args.time_mode}\n\n")
            log.flush()
            result = subprocess.run(cmd, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            print(f"ERROR: {case} exited with code {result.returncode}. See {workspace / 'execution.log'}", file=sys.stderr)
            return result.returncode
        print(f"{case}: completed; inspect {workspace / 'results'} and execution.log", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
