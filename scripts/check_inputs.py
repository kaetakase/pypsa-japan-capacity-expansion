#!/usr/bin/env python3
"""Read-only, standard-library static checks of FY2040 input CSVs.

These checks cannot validate physical assumptions or prove that a PyPSA solve is correct.
"""
import csv
import hashlib
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
IN = ROOT / "input"
FILES = ["load_2040.csv", "solar_pu_2040.csv", "wind_on_pu_2040.csv", "wind_off_pu_2040.csv", "hydro_pu_2040.csv", "geothermal_pu_2040.csv", "biomass_pu_2040.csv", "nuc_pu_2040.csv"]
errors = []
for name in FILES:
    path = IN / name
    if not path.exists():
        errors.append(f"Missing file: {name}")
        continue
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c != "snapshot"]
        dates = []
        lo, hi = float("inf"), float("-inf")
        count = 0
        for row in reader:
            count += 1
            dates.append(row["snapshot"])
            for c in cols:
                v = row[c].replace(",", "").strip()
                try:
                    val = float(v)
                    if not (val == val):
                        errors.append(f"NaN: {name} at row {count} column {c}")
                        break
                except ValueError:
                    errors.append(f"Non-numeric value: {name} at row {count} column {c}")
                    break
                lo, hi = min(lo, val), max(hi, val)
                if name != "load_2040.csv" and not (0 <= val <= 1):
                    errors.append(f"Invalid p.u. value: {name}, row {count}, {c}")
    if len(dates) != len(set(dates)):
        errors.append(f"Repeated timestamps: {name}")
    if count != 8760:
        errors.append(f"Unexpected row count: {name}, {count} rather than 8760")
    print(f"{name}: {count} rows, min={lo:.5f}, max={hi:.5f}")

w1,w2=(IN/"wind_on_pu_2040.csv"),(IN/"wind_off_pu_2040.csv")
if w1.exists() and w2.exists() and hashlib.sha256(w1.read_bytes()).digest()==hashlib.sha256(w2.read_bytes()).digest():
    print("WARNING: Wind onshore and offshore input profile files are IDENTICAL")

policy=IN/"policy_2040.csv"
if policy.exists():
    with policy.open(newline="",encoding="utf-8-sig") as f:
        values={row["parameter"]:row["value"] for row in csv.DictReader(f)}
    for key in ("use_co2_intensity_constraint","use_basic_mix_constraint","carbon_price"):
        print(f"Active policy {key}: {values.get(key, '<missing>')}")

if errors:
    print("FAILED checks:")
    for error in errors[:30]:
        print(" -",error)
    raise SystemExit(1)
print("Static file checks PASS (physical/scientific assumptions are NOT verified).")
