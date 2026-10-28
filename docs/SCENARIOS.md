# Scenario matrix for the paper

The received Python code is a **single-case executable**. It does not automatically run the six cases. It reads the active `input/technology_cost_2040.csv`, `input/capacity_expansion_2040.csv`, `input/policy_2040.csv` and (if enabled) `input/basic_mix_2040.csv`.

The following matrix is a **planned interpretation to verify with the authors' actual run records**, NOT proof that the six paper cases were generated from these settings:

| Paper case | Cost file to make active as `technology_cost_2040.csv` | CO2 intensity cap | Annual generation-share limits |
| --- | --- | --- | --- |
| WG | `technology_cost_2040WG.csv` | OFF | OFF |
| REI | `technology_cost_2040.csv` | OFF | OFF |
| WG-CO2 | `technology_cost_2040WG.csv` | ON, 0.04 tCO2/MWh-load | OFF |
| REI-CO2 | `technology_cost_2040.csv` | ON, 0.04 tCO2/MWh-load | OFF |
| WG-SEP | `technology_cost_2040WG.csv` | ON, 0.04 tCO2/MWh-load | ON, see basic_mix_2040.csv |
| REI-SEP | `technology_cost_2040.csv` | ON, 0.04 tCO2/MWh-load | ON, see basic_mix_2040.csv |

**Do not overwrite or discard source files** when creating cases. Use separately named case folders/scripts so each scenario can be reproduced automatically without manual copying. The other capacity cost alternatives (`...LOW.csv`, `...HIGH.csv`, `...REIOLD.csv`) are currently inactive and are included for provenance only until assigned to specific cases.

The code allows four time modes through `CE_TIME_MODE`: `rep4`, `rep8`, `rep10` and `full8760`. The default is `rep4`. It is important to confirm which mode was used for each result in the paper.

### Policy activation details

When the `input/policy_2040.csv` key `use_co2_intensity_constraint` is `True`, the code uses the target specified by `co2_intensity_tco2_per_mwh` (lowercase), if present; otherwise it uses the in-code default of 0.04. `use_basic_mix_constraint=True` activates basic mix constraints using the CSV. `carbon_price` in the policy file overrides the code's default price; the bundled policy currently sets it to zero. Whether an exogenous carbon price belongs in the objective must be checked against the paper.

### Basic mix bounds as actually supplied

| Category | Lower | Upper |
| --- | ---: | ---: |
| renewable | 40% | 50% |
| nuclear_thermal | 50% | 60% |
| solar | 22% | 29% |
| wind | 4% | 8% |
| hydro | none | 11% |
| geothermal | none | 2% |
| biomass | none | 6% |

All percentages are relative to annual **load**, not gross generation. `renewable` includes the five other renewable categories, so it overlaps their membership by design.
