# Policy-file key capitalization and activation

The original model reads `input/policy_2040.csv`, not `input/policy_2040_intensity.csv`.

The model recognizes the exact lowercase key `co2_intensity_tco2_per_mwh`. The supplied `policy_2040_intensity.csv` originally used uppercase `CO2_INTENSITY_TCO2_PER_MWH` and therefore silently fell back to the model's default `0.04` whenever the lowercase activation flag was `True`. This did not by itself disable the CO2 constraint in historical runs.

For clarity, this release corrects that supplementary reference CSV to:

```csv
parameter,value
carbon_price,0
use_co2_intensity_constraint,True
co2_intensity_tco2_per_mwh,0.04
```

**Important subtlety:** In the unmodified model source, the mere presence of the lowercase `co2_intensity_tco2_per_mwh` parameter automatically activates the CO2 constraint. Do not write that parameter into a supposedly unconstrained policy file. The six-case runner automatically handles this by omitting it from unconstrained cases.
