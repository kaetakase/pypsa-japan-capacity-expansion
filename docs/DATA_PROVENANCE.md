# Data Sources and Preprocessing

**Status: Research draft (October 2026).** This document summarizes the data sources, transformations, and assumptions described in the manuscript *Estimating Japan's 2040 Power System Using a Capacity Expansion Model* (Japanese technical-paper draft, Sections 2-3 and references). It is a documentation of the stated methodology, **not an independent audit of every input CSV**. Source-to-file tracing, redistribution permissions, and full-year numerical reproduction remain to be checked where indicated.

## Model scope

The model represents nine Japanese electricity transmission areas: Hokkaido, Tohoku, Tokyo, Chubu, Hokuriku, Kansai, Chugoku, Shikoku, and Kyushu. Okinawa is not represented. The reference year is FY2040, with hourly resolution (8,760 hours); representative-week options are also available. The model minimizes annualized generation, storage, and interregional transmission investments together with variable operating costs [manuscript, Sections 2.1-2.4].

## 1. Hourly electricity demand

**Original hourly data:** Renewable Energy Institute (REI), *Electricity Supply and Demand Chart* [9], using actual regional demand profiles for FY2024.

**Behind-the-meter solar PV self-consumption correction:** The demand figures in the source chart do not include on-site consumption of solar PV electricity. The manuscript assumes that self-consumed PV electricity equals **19% of reported solar PV generation** and adds this estimated amount to the FY2024 hourly demand data in each region and hour. The resulting demand series is used as the regional hourly demand shape. The manuscript refers to 'various sources' for the 19% assumption but does **not identify a specific supporting reference** for this percentage; the origin and empirical scope of this assumption require further documentation.

**FY2040 annual demand:** The manuscript adopts a national reference of **1,100 TWh for all ten electricity areas including Okinawa**, drawing on the Organization for Cross-regional Coordination of Transmission Operators (OCCTO) future electricity demand scenario [25]. Regional FY2040 demand is estimated by a regression using population as the explanatory variable and historical regional demand/population relationships. Projections are adjusted so the ten-area total is 1,100 TWh. Each region's corrected FY2024 hourly demand shape is then scaled to its projected FY2040 annual electricity demand. Because **Okinawa is outside the nine-node model**, 1,100 TWh is a ten-area reference and must not automatically be interpreted as the nine-area model load total. The precise historical population data, future population projections, and coefficients are not individually cited in the manuscript.

**Important interpretation:** The 19% factor is a correction for estimated PV self-consumption, **not** a 19% uplift applied indiscriminately to every hour of electricity demand or to the 1,100 TWh target. The correction is calculated from the corresponding hourly PV generation profile, before demand-shape scaling. See manuscript Section 3.5.

## 2. Hourly generation availability / per-unit (p.u.) profiles

**Original data:** REI, *Electricity Supply and Demand Chart* [9], FY2024 hourly generation by region and generation technology.

The manuscript constructs hourly generation-per-installed-capacity profiles (p.u.) for solar PV, wind, hydro, geothermal, biomass, and nuclear generation, and provides them exogenously to the model [manuscript, Section 3.6].

**PV adjustment:** Before deriving solar PV p.u. profiles, the manuscript also **adds estimated self-consumed PV generation equal to 19% of reported PV generation** to the hourly generation observations. Thus, the described preprocessing makes adjustments on **both sides of the accounting balance**: (a) the demand time series and (b) the solar PV generation time series. This avoids treating the added self-consumed demand as unserved grid demand. The 19% factor is an assumption, not a directly measured time series.

**Implementation-specific simplification (from the repository README, not independently established by the manuscript citation):** The current draft uses the same hourly p.u. time series for onshore, fixed-bottom offshore and floating offshore wind. Capital cost and capacity restrictions can differ. This is a provisional modeling simplification and does not imply identical real-world wind-resource profiles.

## 3. Existing generation and storage capacity; nuclear assumptions

**Source for FY2024 installed capacities:** REI, *Electricity Supply and Demand Chart* [9]. For existing generation, batteries, pumped hydro, and regional interconnections, the manuscript uses the maximum regional installed-capacity values reported for FY2024 as a starting point, with separate directional-flow treatment for interconnectors described below [Section 3.2].

**Nuclear in FY2040:** The 2040 mid-case assumption in Gisler [10] is adopted, with nuclear capacity fixed consistently across all six scenarios. Nuclear, large hydropower, and pumped hydro are not allowed to expand; their operation is optimized within the existing/fixed capacities. Other represented technologies can expand subject to applicable constraints [Section 3.2].

## 4. Capacity expansion bounds and renewable potential

**Potential data:** Japan's Ministry of the Environment, REPOS renewable-energy potential database [11].

- **Solar PV, wind, geothermal, medium hydro, and small hydro:** regional expansion capacity upper bounds are set at **30% of the corresponding regional technical introduction potential** reported in REPOS [11].
- **Biomass:** the regional total capacity upper bound is set at **1.5 times existing regional capacity**.
- **Battery storage (power):** regional power-capacity upper bound is set at **ten times the upper bound of total regional solar PV capacity**. This was intended as a loose cap rather than a tightly constraining scenario assumption.
- **Battery storage (energy):** the upper bound on storage energy capacity is set at **three hours multiplied by the storage power-capacity upper bound**. This describes the upper-bound methodology; it should not be confused with a statement that every optimal battery installation necessarily operates at three-hour duration.
- **Non-expandable:** nuclear power, large hydro, and pumped hydro, as described above.

These are *modeling assumptions derived from, or applied to, source data*, not direct source estimates of feasible deployment. Source: manuscript Section 3.2 and Table 2.

## 5. Generation, storage, and fuel cost assumptions

### 5.1 WG technology-cost case

**Source:** Agency for Natural Resources and Energy (ANRE), Generation Cost Verification Working Group, *Power Generation Cost Review Sheet* [8], 2025. The WG case uses the default assumptions to derive annual fixed costs (JPY per MW-year) and generation variable costs (JPY per MWh). **Policy-related costs are excluded for all technologies**, based on the discussion in REI [12].

### 5.2 REI technology-cost case

REI uses the WG assumptions except for the following technologies:

- **Solar PV, onshore wind, and battery storage:** cost assumptions from Takase et al., *An Energy Scenario for Japan Towards 2040: Focused on Efficiency Improvements and Renewable Energy*, *Energy Policy* (2026), article 115398 [13].
- **Fixed-bottom offshore wind:** cost assumptions based on REI and Aegir Insights' assessment of offshore wind cost drivers and 2040 projections for Japan [14].
- **Floating offshore wind:** assumed to cost **1.5 times the fixed-bottom offshore wind cost**. This is an explicit model assumption, not a separate offshore cost observation.
- **Other technologies:** same technology cost assumptions as WG.

See manuscript Section 3.2.

### 5.3 Fuel costs used in the manuscript

The fuel prices are based on the WG 2040 projections [8]. The paper uses an exchange rate of **JPY 141 per USD** and specifies the following assumptions (Section 3.4, Table 4):

| Fuel | Assumption as cited in the manuscript | Converted assumption |
| --- | ---: | ---: |
| Coal | 115.40 USD/t | 16,271 JPY/t |
| Natural gas (LNG) | 9.54 USD/MMBtu | 69,600 JPY/t-LNG |
| Oil | 104.60 USD/bbl | 92.8 JPY/L |
| Ammonia | 22.40 USD/MMBtu | 67.4 JPY/kg |
| Hydrogen | 28.70 USD/MMBtu | 544.6 JPY/kg |
| Biomass | 7.22 USD/MMBtu | 12.7 JPY/kg |

Conversion assumptions in the paper include 1 MMBtu = 1.055 GJ, LNG heating value = 54.6 GJ/t, 1 barrel = 158.987 L, ammonia = 22.5 MJ/kg, hydrogen = 142 MJ/kg, and woody biomass = 13.21 MJ/kg. The paper compares its model assumptions with actual historical coal, LNG and oil prices, citing JOGMEC [22] and published customs-statistics summaries [23, 24]. **Those historical-price comparison sources are not necessarily the sources of model input values.**

## 6. Interregional transmission

**Existing directional transfer capacity:** Estimated from the maximum observed directional interregional transfers in FY2024 (manuscript Section 3.3). Interregional transmission expansion is an investment option, with no binding overall expansion upper bound assumed in the manuscript. The model also includes a prospective **Hokkaido-Tokyo long-distance HVDC** corridor, initialized with zero existing transfer capacity.

**Expansion costs:** Route-specific annualized investment costs are assumed, using a **40-year lifetime and 3% interest rate**. Public OCCTO planning documents are cited where available [16-21]; for other routes the HVDC unit cost in the OCCTO grid master plan [15] serves as the reference. The following route values are transcribed from manuscript Table 3 (they have **not** been reconciled line by line with the bundled CSVs):

| Directional route (forward direction shown) | Existing forward GW | Existing reverse GW | Expansion cost, million JPY/MW-year | Source in manuscript |
| --- | ---: | ---: | ---: | --- |
| Hokkaido - Tohoku | 1.2 | 0.8 | 10.4 | [16] |
| Hokkaido - Tokyo (new) | 0 | 0 | 32.5 | [17] |
| Tohoku - Tokyo | 8.3 | 0 | 1.46 | [18] |
| Tokyo - Chubu | 3.0 | 3.4 | 8.91 | [19] |
| Chubu - Hokuriku | 3.0 | 3.0 | 3.24 | [15] |
| Hokuriku - Kansai | 3.0 | 2.6 | 3.24 | [15] |
| Chubu - Kansai | 3.0 | 6.8 | 0.85 | [20] |
| Kansai - Chugoku | 2.6 | 4.8 | 2.6 | [15] |
| Kansai - Shikoku | 0.001 | 0.7 | 2.6 | [15] |
| Chugoku - Shikoku | 0.6 | 1.5 | 2.6 | [15] |
| Chugoku - Kyushu | 0.3 | 3.1 | 19.1 | [21] |

## 7. Policy constraints and scenario definitions

Six scenarios vary the technology-cost assumptions (WG versus REI) and policy restrictions:

| Case | Cost assumptions | Annual CO2 intensity cap | SEP-like generation-share bounds |
| --- | --- | --- | --- |
| WG | WG | No | No |
| REI | REI | No | No |
| WG-CO2 | WG | 0.04 kg-CO2/kWh | No |
| REI-CO2 | REI | 0.04 kg-CO2/kWh | No |
| WG-SEP | WG | 0.04 kg-CO2/kWh | Yes |
| REI-SEP | REI | 0.04 kg-CO2/kWh | Yes |

**Annual CO2 intensity cap:** 0.04 kg-CO2/kWh (equivalent to 0.04 t-CO2/MWh or 40 g-CO2/kWh), as stated in manuscript Section 3.1. The total annual emissions cap is derived from the annual demand. Technology-specific emission factors are model inputs, but the manuscript does not provide a full source-by-source citation for every emission factor.

**SEP-like bounds:** The manuscript cites the Seventh Strategic Energy Plan context [1] and reports indicative electricity-share ranges or values for all renewables (40-50%), solar PV (22-29%), wind (4-8%), hydro (11%), geothermal (2%), biomass (6%), and thermal plus nuclear (50-60%). **Shares are defined as annual electricity production divided by annual electricity demand, not gross annual generation.** The model does not impose a separate nuclear generation-share bound because nuclear capacity is fixed. Read the actual scenario input CSV for the precise lower and upper bound type: the manuscript's reference values should not be misread as equality constraints. Sources: Sections 3.1 and Table 1.

## 8. Representative weeks (used to test time aggregation)

The model supports four, eight, or ten selected 168-hour representative weeks in addition to a full 8,760-hour FY2040 run. Representative hours have equal annualization weights within each configuration. The manuscript identifies the following starting dates (midnight) and reasons (Section 3.7, Table 6):

| Start date | Reason | 4-week | 8-week | 10-week |
| --- | --- | :---: | :---: | :---: |
| 2040-04-29 | Spring solar surplus | Yes | Yes | Yes |
| 2040-05-15 | Kyushu solar surplus | No | Yes | Yes |
| 2040-06-28 | Typical annual supply-demand conditions | No | Yes | Yes |
| 2040-08-03 | Summer demand and low wind | Yes | Yes | Yes |
| 2040-08-20 | Summer evening ramp | No | No | Yes |
| 2040-09-10 | High autumn residual load | No | Yes | Yes |
| 2040-11-15 | Tokyo-Chubu and Chubu-Hokuriku transmission value | No | No | Yes |
| 2040-12-23 | High-wind interregional transfers | Yes | Yes | Yes |
| 2041-01-06 | Low renewables and high load | Yes | Yes | Yes |
| 2041-02-01 | High winter wind and low solar | No | Yes | Yes |

The study uses the full 8,760-hour configuration for its principal results because representative-week estimates do not necessarily converge monotonically to the full-year system composition or cost (manuscript Section 5). These representative-week results should not be presented as identical to the manuscript's main full-year results.

## 9. Source-documentation and redistribution items still open

1. Identify the specific publications or analysis supporting the **19% PV self-consumption** assumption, currently described only as based on 'various sources'.
2. Identify the historical and projected regional population datasets and regression parameters used to allocate FY2040 demand.
3. Confirm exact original data, processing scripts, and permission to redistribute every input CSV; citing a publicly accessible webpage does **not** by itself grant a redistribution license.
4. Confirm that generated hourly demand, hourly PV profiles, capacity limits, technology-cost inputs and directional transmission data correspond to the preprocessing described above; the manuscript does not establish an audited source-to-file mapping.
5. Document the underlying sources and conversion of technology-specific CO2 emission factors and any assumptions not explicitly attributed in the manuscript.
6. Verify exact input CSV implementations of generation-share *upper/lower bounds*, including technologies for which the manuscript supplies a single indicative percentage.
7. Record software versions, model release/tag and a reference-results summary after full-year numerical reproduction is verified. The six four-representative-week cases have been run successfully, but this is separate from verifying the manuscript's 8,760-hour results.

## References (numbers follow the manuscript)

[1] Agency for Natural Resources and Energy (ANRE), *Outlook for Energy Supply and Demand in FY2040 (related materials)*, 2025: https://www.enecho.meti.go.jp/category/others/basic_plan/pdf/20250218_03.pdf

[8] ANRE, Generation Cost Verification Working Group, *Power Generation Cost Review Sheet*, 2025: https://www.enecho.meti.go.jp/committee/council/basic_policy_subcommittee/mitoshi/cost_wg/pdf/cost_wg_20250206_03.xlsx

[9] Renewable Energy Institute (REI), *Electricity Supply and Demand Chart*: https://www.renewable-ei.org/statistics/electricity/#demand

[10] Romain Gisler, *Japan's Nuclear Power: Challenges in Achieving the FY2030/FY2040 Targets*, REI, 2026: https://www.renewable-ei.org/activities/column/REupdate/20260424.php

[11] Ministry of the Environment, *Renewable Energy Potential Information System (REPOS)*: https://repos.env.go.jp/web/

[12] Kimura et al., *Problems with the Assumptions Used in the 2024 Power Generation Cost Verification*, REI, 2025: https://www.renewable-ei.org/pdfdownload/activities/REI_LCOE_report_2503.pdf

[13] Takase, K., Kimura, S., Nishida, Y., Saito, T., and Wakiyama, T., *An Energy Scenario for Japan Towards 2040: Focused on Efficiency Improvements and Renewable Energy*, *Energy Policy* (2026), article 115398: https://doi.org/10.1016/j.enpol.2026.115398

[14] REI and Aegir Insights, *Cost Drivers and the 2040 Outlook for Fixed-Bottom Offshore Wind Power in Japan*, 2026: https://www.renewable-ei.org/activities/reports/20260527.php

[15] OCCTO, *Long-term Cross-regional Network Policy (Grid Master Plan)*, 2023: https://www.occto.or.jp/news/kouikikeitou_chokihoushin_230329_choukihoushin_sakutei.html

[16] OCCTO, *Replacement of the First Pole of the Hokkaido-Honshu Interconnection*, 2025: https://www.occto.or.jp/assets/iinkai/kouikikeitouseibi/2025/files/seibi_90_02_01.pdf

[17] OCCTO, *Overall Progress on Cross-regional Grid Development Plans*, 2025: https://www.occto.or.jp/assets/soukaihoka/hyougiinkai/2024/files/2024_4_houkoku_1.pdf

[18] OCCTO, *Projected Transfer Capacity after Tohoku-Tokyo Interconnection Expansion*, 2024: https://www.occto.or.jp/assets/iinkai/kouikikeitouseibi/2024/files/seibi_85_02_01.pdf

[19] OCCTO, *Cross-regional Grid Development Plan for the Tokyo-Chubu Interconnection*, 2019: https://www.occto.or.jp/assets/kouikikeitou/seibikeikaku/tokyochubu/files/FC__20190327.pdf

[20] OCCTO, *Cross-regional Grid Development Plan for the Chubu-Kansai Interconnection*, 2024: https://www.occto.or.jp/assets/kouikikeitou/seibikeikaku/chubukansai/files/20240628_seibikeikaku.pdf

[21] OCCTO, *Cross-regional Grid Development Plan for the Chugoku-Kyushu Interconnection*, 2025: https://www.occto.or.jp/assets/kouikikeitou/seibikeikaku/kanmon/files/20251015_seibikeikaku.pdf

[22] JOGMEC, *Natural Gas and LNG Prices (May 2026 preliminary)*: https://journal.jogmec.go.jp/oilgas/nglng/spotprice/202605.html

[23] Energy Information Center, *Coal Customs Price Statistics*: https://pps-net.org/statistics/coal3

[24] Energy Information Center, *Crude Oil Customs Price Statistics*: https://pps-net.org/statistics/crude-oil3

[25] OCCTO, *Report on the Study Group on Future Electricity Supply and Demand Scenarios*, 2025: https://www.occto.or.jp/houkokusho/2025/2025_shorai_jukyu_houkokusyo.html

*Reference names and URLs above were transcribed from the supplied manuscript. External URLs and underlying source-data permissions have not been independently verified for this draft.*
