# PRE-RELEASE SCIENTIFIC CHECKS

**Do not make this draft public until the blocking items are cleared.** This list is an audit of the user-provided code and input files. No full model solve was executed in this audit.

## Blocking checks

- [ ] **Regional demand assignments**: The supplied `load_2040.csv` has Chubu ~39.17 TWh/year and Hokuriku ~168.96 TWh/year. Recheck the regional demand assignment and the source calculation; compare to region-specific FY2024 and FY2040 assumptions.
- [ ] **Six-case reproducibility**: Create runnable, documented settings for WG, REI, WG-CO2, REI-CO2, WG-SEP, REI-SEP. Current active `policy_2040.csv` turns both constraints off. Create a six-case results table demonstrating the paper's values.
- [ ] **Nuclear assumptions**: Nuclear capacity is non-extendable. In the input, Hokkaido and Tokyo have nonzero existing nuclear capacity yet all-zero 8760h `nuc_pu` availability. Clarify if 2040 availability intentionally reflects the base-year observed dispatch rather than future reopening.
- [ ] **License and input redistribution**: Verify permission to publish the project code and each CSV, especially the source statistics and any derived external data.
- [ ] **Environment**: Record Python, PyPSA, Linopy, highspy/HiGHS, pandas, NumPy, xarray versions from the working research machine; test with a clean environment.
- [ ] **Representative-week run**: Check that selected time periods and SOC-boundary constraints execute and that results are labeled accurately.
- [ ] **Full-year run**: Verify an optimal 8760h run and compare key numeric outputs to the manuscript.

## Important explanatory checks

- [x] **Shared onshore/offshore wind profile is intentional and provisional**: The researcher confirms both input p.u. series are identical by design at this stage. README and provenance note the approximation; technology-specific wind output patterns are not represented. Before publication, ensure the manuscript mentions this limitation.

- [ ] Code defaults to `rep4` (not 8760h) and `CASE_LABEL=rei_cp4300_nucmid`, but `policy_2040.csv` has `carbon_price=0`; default case label is misleading.
- [ ] `policy_2040_intensity.csv` contains `CO2_INTENSITY_TCO2_PER_MWH` in uppercase. The input parser looks for lowercase `co2_intensity_tco2_per_mwh`. An explicit `use_co2_intensity_constraint=True` activates the code's default 0.04; changing the uppercase value alone will not update the target. Fix the key in a validated revision.
- [ ] In `basic_mix_2040.csv`, hydro (11%), geothermal (2%), biomass (6%) have upper bounds only; they are not fixed shares. Check the manuscript wording.
- [x] Onshore, offshore fixed and offshore floating wind use the same hourly p.u. data as a documented, temporary simplification; do not present these as technology-specific resource profiles.
- [ ] Some regions have `geothermal_pu` identically zero, which can prevent additional geothermal generation even if capacity expansion is allowed; check spatial potential assumptions.
- [ ] Separately document the exogenous carbon price and CO2-cap shadow price interpretation. The dual of `Policy-co2_intensity` is in JPY/tCO2 as implemented, and is an *additional* constraint value beyond any exogenous carbon price.
- [ ] The nuclear capacity assumption is a fixed `p_nom`, not a modeled nuclear investment variable; an ``Generator-ext-p_nom-upper`` dual for nuclear will not exist. Use explicit sensitivity runs if evaluating marginal cost of nuclear capacity restrictions.
- [ ] The generation-mix categories are defined in `basic_mix_2040.csv` by `category` and optional `carriers`, or in `BASIC_MIX_DEFAULT_CARRIER_GROUPS`. Annual load (MWh) is the denominator. ``nuclear_thermal`` has an explicit carriers list.
- [ ] Output field names `Record` and `Plan` in chart power-flow CSV currently point to the same computed series, not independently observed/forecast values; avoid a misleading public description.
- [ ] Explain `2024 reference-year max observed dispatch` normalization for p.u. where relevant and that observed output is not identical to physical availability.
- [ ] Source for assumed 19% rooftop solar self-consumption and potential double counting must be documented and verified against the construction of `load_2040.csv`/`solar_pu_2040.csv`.

## Before manuscript submission

- [ ] Include exact data citations and preprocessing scripts if the latter exist.
- [ ] Include a model/assumptions table describing capital cost, region-specific capacity constraints, hourly profile definitions and energy conversion units.
- [ ] Specify the executable version / release tag and a full set of outputs with objective values, emissions, generation shares, binding constraints and solver status.
- [ ] Cross-check figure and table values, especially wind technology breakdown and share constraint shadow prices.
