# Historical results archive: partial verification

The separately provided `results.zip` was checked against its `results_csv/model_settings.csv` and `cost_summary.csv` where present. The archive is **not** part of this Git repository, and these are **previous results**, not newly re-run outputs from the scenario runner.

| Likely paper scenario | Historical folder in external archive | Annual system cost (trillion JPY) | Actual CO2 intensity (tCO2/MWh-load) | Status |
|---|---|---:|---:|---|
| WG | `WG_0_MID_8760` | 6.75 | 0.630 | Baseline settings in archive: CO2 OFF, mix OFF |
| REI | `REI_0_MID_8760` | 6.48 | 0.420 | Baseline settings in archive: CO2 OFF, mix OFF |
| REI-CO2 (provisional association) | `REI_0.04_MID_8760_sp` | 8.35 | 0.040 | CO2 ON, mix not recorded; internal `SCENARIO_NAME` includes **wg** despite the enclosing folder being named REI |
| REI-SEP | `REI_0.04_MID_SEP_8760` | 10.91 | 0.040 | CO2 ON, mix ON; CO2 dual available |
| WG-CO2 | Not positively identified | -- | -- | No unambiguous corresponding result in the supplied archive |
| WG-SEP | Not positively identified | -- | -- | No unambiguous corresponding result in the supplied archive |

Observations:

- `REI_0.04_MID_8760_sp` contains a `Policy-co2_intensity` dual of approximately 24,571 JPY/tCO2, and `REI_0.04_MID_SEP_8760` about 35,488 JPY/tCO2; these are consistent with the values reported in the manuscript.
- **A folder name or case label is not proof of which technology cost CSV was active.** The original output only captures some settings, not checksums of the input cost CSV. Consequently the table above is a **tentative association** for existing outputs.
- Until each case is re-run from a dated set of source inputs and compared to the manuscript figures, do not claim that all six study cases have been reproduced.
- For a robust verification, compare total annual cost, CO2 emissions, technology-level output shares, total and new capacity, and binding share constraints and their dual values for each of the six staged runs.
