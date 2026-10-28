# Data provenance and redistribution permission review

The files in `input/` were supplied with the research project. Their authoritative sources and licenses were not independently verified as part of the repository packaging. Before any public upload, populate the source, preprocessing method, original download URL, attribution statement, data license and permission to redistribute for every data class.

| Input group | Files | Source/permission status |
| --- | --- | --- |
| Load and profile data | `load_2040.csv`, `solar_pu_2040.csv`, `wind_on_pu_2040.csv`, `wind_off_pu_2040.csv`, `hydro_pu_2040.csv`, `geothermal_pu_2040.csv`, `biomass_pu_2040.csv`, `nuc_pu_2040.csv` | **Confirm** FY2024 source series, transformations and redistribution rights; manuscript describes use of Renewable Energy Institute Power Supply & Demand Charts |
| Existing capacities and constraints | `capacity_expansion_2040.csv`, `capacity_expansion_2040HIGH.csv`, `capacity_expansion_2040LOW.csv` | **Confirm** generation capacity, REPOS potential and study assumptions |
| Technology costs | `technology_cost_2040.csv`, `technology_cost_2040WG.csv`, `technology_cost_2040REIOLD.csv` | **Confirm** 2025 Cost Verification WG sources, REI study assumptions and data rights |
| Interconnectors | `lines_expansion_2040.csv` | **Confirm** OCCTO and study-specific costs and limits |
| Fuel and carbon | `fuel_price_2040.csv`, `emission_factor_2040.csv` | **Confirm** cited forecast, emissions conventions and units |
| Policy scenario values | `policy_2040.csv`, `policy_2040_intensity.csv`, `basic_mix_2040.csv` | Author-provided scenario controls, **confirm** correspondence to the submitted paper |

**Wind-profile assumption:** `wind_on_pu_2040.csv` and `wind_off_pu_2040.csv` deliberately contain the same hourly values as a provisional modeling simplification. This choice does not imply that resource conditions or realized output are identical for onshore, fixed-bottom offshore and floating offshore turbines. Future analysis may introduce separate profiles; the source and normalization process should be documented before release.

A code license does NOT automatically establish permission to redistribute input data. If redistribution permission is unclear, consider publishing the preprocessing method plus links to sources rather than the derived CSV themselves, and avoid describing the project as 'fully reproducible' until the missing data can be obtained lawfully.

Prior to release, identify who owns the code (institution versus authors), agree on an explicit open-source license for software (e.g. MIT if approved), and specify a separate dataset license if applicable. Do not apply an open license to third-party data without authorization.
