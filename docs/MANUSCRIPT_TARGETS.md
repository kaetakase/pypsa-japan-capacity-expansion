# Manuscript benchmark targets (rounded, not independently reproduced)

These rounded target results are transcribed from the current manuscript draft. They are provided for **comparison when the model has been re-run**; they are *not* outputs from the new case runner.

| Case | Annual system cost (trillion JPY/year) | Annual CO2 intensity (kgCO2/kWh-load) | CO2 policy constraint shadow price (10,000 JPY/tCO2) |
|---|---:|---:|---:|
| WG | 6.8 | 0.63 | not applicable |
| REI | 6.5 | 0.42 | not applicable |
| WG-CO2 | 11.8 | 0.04 | 3.6 |
| REI-CO2 | 8.3 | 0.04 | 2.5 |
| WG-SEP | 12.1 | 0.04 | 4.0 |
| REI-SEP | 10.9 | 0.04 | 3.5 |

**Cautions**

- Values are rounded. Do not claim exact match based only on one decimal place.
- The calculations used to draft the manuscript may differ from the current distributed code and input files. Confirm the active input CSV checksums and solver versions from original runs.
- Besides system cost and CO2 intensity, independently compare annual electricity generation mix and technology capacity against the paper figures.
- Verify whether an exogenous carbon price is already included in variable costs. The six-case matrix here uses `carbon_price=0` as indicated by the supplied policy CSV and archived unconstrained runs.
- Confirm that upper-only hydro, geothermal and biomass generation shares in the source CSV match the numerical experiment and the revised manuscript description.
