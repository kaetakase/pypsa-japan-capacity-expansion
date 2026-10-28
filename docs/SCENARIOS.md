# Six-case scenario configuration (FY2040)

The scenario matrix is the machine-readable source of truth:
[`scenarios/scenario_matrix.csv`](../scenarios/scenario_matrix.csv).

| Paper case | Active technology cost file | CO2 intensity cap | Annual electricity mix share constraints | Carbon price |
|---|---|---|---|---|
| WG | `technology_cost_2040WG.csv` | OFF | OFF | 0 JPY/tCO2 |
| REI | `technology_cost_2040.csv` | OFF | OFF | 0 JPY/tCO2 |
| WG-CO2 | `technology_cost_2040WG.csv` | ON: 0.04 tCO2/MWh-load | OFF | 0 JPY/tCO2 |
| REI-CO2 | `technology_cost_2040.csv` | ON: 0.04 tCO2/MWh-load | OFF | 0 JPY/tCO2 |
| WG-SEP | `technology_cost_2040WG.csv` | ON: 0.04 tCO2/MWh-load | ON: `basic_mix_2040.csv` | 0 JPY/tCO2 |
| REI-SEP | `technology_cost_2040.csv` | ON: 0.04 tCO2/MWh-load | ON: `basic_mix_2040.csv` | 0 JPY/tCO2 |

These settings implement the six **intended** manuscript cases. They have been tested for correct file staging **without solving the PyPSA model**. The costs, outputs and numerical identity to the six final published cases are **not independently validated**.

## Execute without overwriting the source inputs

From the repository root:

```bash
python3 scripts/check_inputs.py
python3 scripts/run_scenarios.py --list
python3 scripts/run_scenarios.py --all --time-mode full8760 --dry-run
```

The dry run creates six isolated working directories under `runs/full8760/`. Inspect one of the staged policy CSVs, for example `runs/full8760/rei-sep/input/policy_2040.csv`.

Once the research Python environment has PyPSA/Linopy/HiGHS installed and validated, execute one scenario first:

```bash
python3 scripts/run_scenarios.py --case REI-CO2 --time-mode rep4 --force
```

To run the study's full-year REI-CO2 case:

```bash
python3 scripts/run_scenarios.py --case REI-CO2 --time-mode full8760 --force
```

Run all six full-year cases only after the initial case succeeds:

```bash
python3 scripts/run_scenarios.py --all --time-mode full8760 --force
```

`--force` removes any previous staged workspace and results **for the selected case and time mode**, not the original `input/` directory. Omit `--force` on the first run or if you wish to keep old results. A failed calculation writes an `execution.log` in that case's workspace. The model's own results will appear under `runs/<time-mode>/<case>/results/<timestamp>_<label>/`.

**Time modes:** full-year (`full8760`) is the manuscript's principal analysis, and `rep4`, `rep8` and `rep10` are representative-week sensitivity analyses. The original model defaults to `rep4`, so the runner explicitly passes the requested time mode.

## Exact policy activation semantics

The original Python parser checks dictionary keys **case sensitively**.

- On a CO2-constrained run, `policy_2040.csv` must contain both `use_co2_intensity_constraint,True` and `co2_intensity_tco2_per_mwh,0.04` (lowercase).
- The original model automatically turns the CO2 constraint **on if the lowercase target key is present**, even if the Boolean switch is false. Therefore, the runner **omits the target key entirely** when the constraint is meant to be OFF.
- `use_basic_mix_constraint,True` enables all rows of `basic_mix_2040.csv`; false disables them.
- `carbon_price,0` sets the exogenous price component to zero in all six cases. This is separate from the endogenous CO2 constraint shadow price.

The distribution copy of `input/policy_2040_intensity.csv` was corrected to use the lowercase target name; it is included for manual reference only. The runner does not rely on it.

## Generation category definitions (from supplied CSV)

The model divides generator *carriers* into categories when applying its electricity-mix constraints. In the provided `basic_mix_2040.csv`:

| Category | Lower share of annual load | Upper share of annual load |
|---|---:|---:|
| renewables overall | 40% | 50% |
| nuclear and thermal | 50% | 60% |
| solar | 22% | 29% |
| wind | 4% | 8% |
| hydro | not specified | 11% |
| geothermal | not specified | 2% |
| biomass | not specified | 6% |

Hydro/geothermal/biomass are *upper-only* bounds, not point (exact equality) targets. The denominator is **annual load**, not total gross generation. Category sets intentionally overlap: renewables total contains solar, wind, hydro, geothermal and biomass. `nuclear_thermal` uses its explicit `carriers` list, while other groups use code defaults. Detailed technology mapping: `BASIC_MIX_DEFAULT_CARRIER_GROUPS` in the original model.

## Version and provenance checks

Every isolated run writes `run_manifest.json` with source file names, input SHA-256 values, policy values, time mode and installed package versions. Preserve the relevant manifest and output summary when publishing the paper's reproducibility release.

Please validate assumptions before publishing: regional demand assignments; identical onshore/offshore wind profile (intentional, provisional); nuclear availability; licensing of derived input data; reference-year p.u. normalization; and handling of paper case-specific input versions. Also see `PRE_RELEASE_CHECKS.md`.

## Historical result archive cross-check

See [HISTORICAL_RESULTS_CHECK.md](HISTORICAL_RESULTS_CHECK.md) for the limited verification possible from the separately provided `results.zip`, and [MANUSCRIPT_TARGETS.md](MANUSCRIPT_TARGETS.md) for rounded comparison targets from the draft manuscript. The archive does not establish a complete six-case reproduction.
