# PyPSA Japan Capacity Expansion Model (Research Draft)

This repository contains a PyPSA-based 9-region capacity expansion model of Japan's electricity system, using an FY2040 hourly demand scenario and renewable-generation profiles. It is intended to make model assumptions, inputs, policy constraints, and shadow prices available for examination and reproduction.

**REVIEW STATUS: NOT YET VALIDATED FOR PUBLIC RELEASE.** The included code and CSV values are copied from the research materials without scientific corrections. See [`docs/PRE_RELEASE_CHECKS.md`](docs/PRE_RELEASE_CHECKS.md) before making this repository public. The model has passed Python syntax checking, but a verified optimization run and reproduction of the six manuscript cases are pending.

## Model at a glance

- Geography: Hokkaido, Tohoku, Tokyo, Chubu, Hokuriku, Kansai, Chugoku, Shikoku, and Kyushu (Okinawa excluded).
- Period: FY2040 (2040-04-01 to 2041-03-31), with 1-hour resolution (8760 snapshots) or 4, 8, or 10 selected representative weeks.
- Optimization: annualized generation, storage and transmission investments plus operation; HiGHS solver using PyPSA/Linopy.
- Policy switches: optional CO2 intensity cap and optional generation mix bounds based on annual load, not annual gross generation.
- Outputs: generator build, annual generation, investment and variable costs, emissions, curtailment, dispatch, regional flows, storage state-of-charge, and selected dual variables.
- Simplifications: no unit commitment or reserve requirement in the supplied configuration, and onshore, fixed-bottom offshore and floating offshore wind intentionally share a common hourly p.u. profile as a **provisional simplifying assumption**. Their cost and capacity parameters can differ, but technology-specific wind availability is not resolved.

## File organization

```text
pypsa_japan_capacity_expansion_2040.py  Main model, unchanged from the submitted text
input/                                  Original 20 CSV inputs (without macOS metadata)
scripts/check_inputs.py                  Static data audit (no optimization)
docs/PRE_RELEASE_CHECKS.md              Scientific and publication checks
docs/SCENARIOS.md                       How the six paper cases must be configured
docs/DATA_PROVENANCE.md                 Source and redistribution-license checklist
requirements-example.txt                Unpinned example dependencies, not an exact lockfile
.gitignore                              Excludes local results and temporary files
```

## Install and run (requires verification)

Python 3.11+ is recommended. Create a dedicated Python environment, then install the model requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-example.txt
```

First inspect the data using the standard-library-only checker:

```bash
python scripts/check_inputs.py
```

Running the original script requires `input/` to be a sibling of the `.py` file, and the process working directory must be this repository root:

```bash
CE_TIME_MODE=rep4 CE_CASE_LABEL=test python pypsa_japan_capacity_expansion_2040.py
```

**CAUTION:** The bundled `input/policy_2040.csv` disables both the CO2 intensity constraint and the electricity mix constraint, and the active technology cost file is the REI variant. The model's default `CASE_LABEL` implies a carbon price of 4,300 JPY/tCO2, but this CSV actually overrides the carbon price to zero. As a result, simply running the above command does NOT reproduce the paper's six scenarios. See [SCENARIOS.md](docs/SCENARIOS.md).

For FY2040 annual analysis, set `CE_TIME_MODE=full8760`, after model and source data have been validated. Large annual optimizations may require significant memory and solve time.

### Results

Results are written to `results/<date>_<case_name>/`. The directory is deliberately ignored by Git. Publish small verification summaries and method details only after checking accuracy and permission to redistribute.

## Reproducibility and scientific limitations

1. The input time series are 8760 hours in FY2040 and have no missing timestamps or invalid p.u. values.
2. `wind_on_pu_2040.csv` and `wind_off_pu_2040.csv` are **identical by design for this provisional research model**. The shared p.u. series is a simplifying proxy, not an assertion that onshore and offshore wind have the same real-world generation pattern. This assumption omits resource and output-profile differences; it is documented here and is a candidate for future sensitivity analysis.
3. `load_2040.csv` shows Chubu at about 39.2 TWh and Hokuriku at about 169.0 TWh; this should be checked before interpreting any results.
4. Installed PyPSA, Linopy, HiGHS and Python package versions must be recorded from the computer used for the paper. No verified environment lockfile is yet available.
5. Key modeling choices including CO2 pricing, hourly p.u. normalization and nuclear availability need to be documented in the paper and the public release.

## License and citations

**No software or data license is granted by this draft.** Before public release, confirm ownership/authorization of code and permission to redistribute every input dataset, then add an explicit software license and appropriate data usage terms. The model relies on third-party scientific software and potentially sourced electricity statistics; cite the original sources rather than assuming all source data may be relicensed.

See [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md). Add the manuscript reference, GitHub permanent release tag, and an archival DOI (if obtained) once validated.
