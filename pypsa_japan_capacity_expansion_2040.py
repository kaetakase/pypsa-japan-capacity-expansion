import os
from datetime import datetime

import pandas as pd
import pypsa
import matplotlib.pyplot as plt
import xarray as xr

# =========================================================
# Unit convention
# =========================================================
# Power:        MW
# Energy:       MWh
# Cost:         JPY
# Time step:    1 hour
#
# PyPSA capital_cost convention used here:
#   Generator / Line / Link / StorageUnit capital_cost = JPY/MW/year
#
# If your source cost is JPY/kW/year:
#   JPY/MW/year = JPY/kW/year * 1000
#
# If your source variable cost is JPY/kWh:
#   JPY/MWh = JPY/kWh * 1000
# =========================================================


# =========================================================
# 0. Scenario settings
# =========================================================

TIME_MODE = os.environ.get("CE_TIME_MODE", "rep4").lower()

# Optional label for result folder names.
# Example:
#   CE_CASE_LABEL=rei_cp4300_nucmid
CASE_LABEL = os.environ.get("CE_CASE_LABEL", "rei_cp4300_nucmid").lower()

REP4_PERIODS = [
    ("spring_solar_surplus", "2040-04-29 00:00", 168),
    ("wind_drought_summer", "2040-08-03 00:00", 168),
    ("high_wind_transfer", "2040-12-23 00:00", 168),
    ("low_vre_high_load", "2041-01-06 00:00", 168),
]

REP8_PERIODS = [
    ("spring_solar_surplus", "2040-04-29 00:00", 168),
    ("kyushu_pv_surplus", "2040-05-15 00:00", 168),
    ("annual_typical", "2040-06-28 00:00", 168),
    ("wind_drought_summer", "2040-08-03 00:00", 168),
    ("high_residual_autumn", "2040-09-10 00:00", 168),
    ("high_wind_transfer", "2040-12-23 00:00", 168),
    ("low_vre_high_load", "2041-01-06 00:00", 168),
    ("winter_high_wind_low_solar", "2041-02-01 00:00", 168),
]

REP10_PERIODS = [
    ("spring_solar_surplus", "2040-04-29 00:00", 168),
    ("kyushu_pv_surplus", "2040-05-15 00:00", 168),
    ("annual_typical", "2040-06-28 00:00", 168),
    ("wind_drought_summer", "2040-08-03 00:00", 168),
    ("summer_evening_ramp", "2040-08-20 00:00", 168),
    ("high_residual_autumn", "2040-09-10 00:00", 168),
    ("chubu_tokyo_transfer", "2040-11-15 00:00", 168),
    ("high_wind_transfer", "2040-12-23 00:00", 168),
    ("low_vre_high_load", "2041-01-06 00:00", 168),
    ("winter_high_wind_low_solar", "2041-02-01 00:00", 168),
]

if TIME_MODE in {"rep4", "representative", "representative_weeks"}:
    SCENARIO_NAME = f"capacity_expansion_2040_rep4_{CASE_LABEL}_carriers"
    REPRESENTATIVE_PERIODS = REP4_PERIODS

elif TIME_MODE in {"rep8", "representative8", "representative_8weeks"}:
    SCENARIO_NAME = f"capacity_expansion_2040_rep8_{CASE_LABEL}_carriers"
    REPRESENTATIVE_PERIODS = REP8_PERIODS

elif TIME_MODE in {"rep10", "representative10", "representative_10weeks"}:
    SCENARIO_NAME = f"capacity_expansion_2040_rep10_{CASE_LABEL}_carriers"
    REPRESENTATIVE_PERIODS = REP10_PERIODS

elif TIME_MODE in {"full", "full8760", "8760"}:
    SCENARIO_NAME = f"capacity_expansion_2040_full8760_{CASE_LABEL}_carriers"

    REPRESENTATIVE_PERIODS = [
        ("full_year", "2040-04-01 00:00", 8760),
    ]

else:
    raise ValueError(
        "Invalid CE_TIME_MODE. Use 'rep4', 'rep8', 'rep10', or 'full8760'. "
        f"Current value: {TIME_MODE}"
    )

TIME_FREQ = "h"

INPUT_DIR = "input"
RESULTS_ROOT = "results"

# ---------------------------------------------------------
# Major input files
# ---------------------------------------------------------
CAPACITY_FILE = "capacity_expansion_2040.csv"
LINES_FILE = "lines_expansion_2040.csv"

LOAD_FILE = "load_2040.csv"
SOLAR_PU_FILE = "solar_pu_2040.csv"
WIND_ON_PU_FILE = "wind_on_pu_2040.csv"
WIND_OFF_PU_FILE = "wind_off_pu_2040.csv"
HYDRO_PU_FILE = "hydro_pu_2040.csv"
GEOTHERMAL_PU_FILE = "geothermal_pu_2040.csv"
BIOMASS_PU_FILE = "biomass_pu_2040.csv"
NUCLEAR_PU_FILE = "nuc_pu_2040.csv"

TECH_COST_FILE = "technology_cost_2040.csv"
FUEL_PRICE_FILE = "fuel_price_2040.csv"
EMISSION_FACTOR_FILE = "emission_factor_2040.csv"
POLICY_FILE = "policy_2040.csv"
BASIC_MIX_FILE = "basic_mix_2040.csv"

# ---------------------------------------------------------
# Solver
# ---------------------------------------------------------
SOLVER_NAME = "highs"

# ---------------------------------------------------------
# Switches
# ---------------------------------------------------------
USE_CARBON_PRICE = True
USE_FUEL_PRICE_BASED_THERMAL_COST = True
USE_RESERVE_CONSTRAINT = False

# Optional DR. This code keeps the same placeholder as your current code.
DR_SHIFT_SHARE = 0.0
DR_SHIFT_EFF_IN = 1.0
DR_SHIFT_EFF_OUT = 1.0
DR_SHIFT_MAX_HOURS = 4.0

# Cost scaling for numerical stability.
# Keep 1.0 unless the solver has numerical issues.
COST_SCALE = 1.0

# Capital-cost weighting.
# With representative weeks, only variable costs are scaled by snapshot_weightings.
# Capital costs are annualized, so do not scale them down.
CAPEX_TIME_WEIGHT = 1.0

# Load shedding penalty (JPY/MWh)
LOAD_SHEDDING_COST = 10_000_000_000.0

# Storage efficiency defaults
BATTERY_CHARGE_EFF = 0.95
BATTERY_DISCHARGE_EFF = 0.95
PHS_CHARGE_EFF = 0.90
PHS_DISCHARGE_EFF = 0.90

DEFAULT_STORAGE_MAX_HOURS = {
    # Cost Verification WG solar+battery assumption: 0.075万kWh / 0.025万kW = 3h.
    "battery": 3.0,
    "phs": 8.0,
}

# Storage SOC handling.
# - full8760: use annual cyclic SOC.
# - representative weeks: do not let storage carry energy from one
#   representative week to another. Instead, SOC is fixed to zero at
#   the start and end of each representative period via additional
#   constraints added before solving.
STORAGE_CYCLIC_SOC = TIME_MODE in {"full", "full8760", "8760"}
REPRESENTATIVE_STORAGE_BOUNDARY_MODE = "zero" if not STORAGE_CYCLIC_SOC else "none"

USDJPY = 141.0

# Cost Verification WG heating values
# coal: 26.08 MJ/kg
# oil: 41.63 MJ/L
# biomass: 13.21 MJ/kg
MWH_PER_MMBTU = 0.29307107
COAL_MMBTU_PER_T = 24.719067
OIL_MMBTU_PER_BBL = 6.273260
BIOMASS_MMBTU_PER_T = 12.520662

# Biomass co-firing assumption for Cost WG-style coal-biomass 5% mass-basis.
# The model fuel mix uses heat-input shares, so the 5% mass share is converted
# to a heat share using representative lower-heating values.
# BIOMASS_MMBTU_PER_T = 14.2  # roughly 15 MJ/kg deleted because it is set in csv
COAL_BIOMASS_MASS_SHARE = 0.05
COAL_BIOMASS_BIOMASS_HEAT_SHARE = (
    COAL_BIOMASS_MASS_SHARE * BIOMASS_MMBTU_PER_T
    / ((1.0 - COAL_BIOMASS_MASS_SHARE) * COAL_MMBTU_PER_T + COAL_BIOMASS_MASS_SHARE * BIOMASS_MMBTU_PER_T)
)
COAL_BIOMASS_COAL_HEAT_SHARE = 1.0 - COAL_BIOMASS_BIOMASS_HEAT_SHARE

# Fallback fuel prices if fuel_price_2040.csv is missing or incomplete.
# Fuel prices are expressed in the units expected by the conversion functions:
#   coal: USD/t
#   oil: USD/bbl
#   gas, hydrogen, ammonia, biomass: USD/MMBtu
#
# For hydrogen and ammonia, these fallback values follow the
# Cost Verification WG-style HHV conversion:
#   overseas blue ammonia: 478 USD/t, HHV 22.5 MJ/kg -> about 22.4 USD/MMBtu
#   overseas blue hydrogen: 4095 USD/t, HHV 142 MJ/kg -> about 30.4 USD/MMBtu
#
# Prefer overriding these in fuel_price_2040.csv for scenario-specific assumptions.
FOSSIL_FUEL_PRICE = {
    "oil_usd_per_bbl": 80.0,
    "coal_usd_per_t": 99.1,
    "gas_usd_per_mmbtu": 8.7,
    "ammonia_usd_per_mmbtu": 22.4,
    "hydrogen_usd_per_mmbtu": 30.4,
    "biomass_usd_per_mmbtu": 10.0,
}

# Carbon price (JPY/tCO2)
CARBON_PRICE_JPY_PER_TCO2 = 4300.0


# =========================================================
# 0.1 Technology definitions aligned with Cost Verification WG
# =========================================================
# The key change from the previous model:
#
# Old carrier examples:
#   gas_ccgt, gas_ocgt, solar, wind_on, wind_off
#
# In this version, gas_ccgt/gas_ocgt are kept unchanged.
# Solar is split into utility/residential.
# Onshore wind keeps the existing name wind_on.
# Offshore wind is split into short names: wind_off_fx and wind_off_fl.
#
# CCS / co-firing technologies are represented as separate carriers.
# This keeps the CE model linear and makes cost and shadow-price outputs easy
# to interpret.

# Thermal carriers and their fuel mix on a heat-input basis.
# Shares should sum to 1.0.
# For ammonia/hydrogen co-firing, fuel prices are blended by heat share.
THERMAL_FUEL_MIX = {
    # Conventional fossil
    "coal": {"coal": 1.0},
    "oil": {"oil": 1.0},
    "gas_ccgt": {"gas": 1.0},  # gas combined cycle
    "gas_ocgt": {"gas": 1.0},  # gas open cycle / simple cycle

    # Dedicated zero-carbon fuel generation. These are treated as thermal generators
    # with externally supplied fuel prices, not as fuel-stock technologies.
    "hydrogen": {"hydrogen": 1.0},
    "ammonia": {"ammonia": 1.0},

    # CCS options
    "coal_ccs": {"coal": 1.0},
    "gas_ccgt_ccs": {"gas": 1.0},

    # Co-firing options. Use ratio-specific carrier names in CSVs.
    # Shares are heat-input shares in the model. For Cost WG biomass 5% mass-basis,
    # this is a simplified approximation unless a heat-basis conversion is supplied.
    "coal_biomass_5": {"coal": COAL_BIOMASS_COAL_HEAT_SHARE, "biomass": COAL_BIOMASS_BIOMASS_HEAT_SHARE},
    "coal_ammonia_20": {"coal": 0.8, "ammonia": 0.2},
    "gas_ccgt_hydrogen_10": {"gas": 0.9, "hydrogen": 0.1},
    
    # Backward-compatible alias. Prefer coal_biomass_5 in input CSVs.
    "coal_biomass": {"coal": COAL_BIOMASS_COAL_HEAT_SHARE, "biomass": COAL_BIOMASS_BIOMASS_HEAT_SHARE},
}

THERMAL_CARRIERS = set(THERMAL_FUEL_MIX.keys())

# Variable O&M defaults (JPY/MWh).
# These are small compared with fuel cost but should differ by technology.
# Override these values by putting marginal_cost in capacity_expansion_2040.csv
# or technology_cost_2040.csv if needed.
# THERMAL_VOM_JPY_PER_MWH = {
#     "coal": 300.0,
#     "coal_ccs": 700.0,
#     "coal_ammonia_20": 500.0,

#     "gas_ccgt": 200.0,
#     "gas_ocgt": 250.0,
#     "gas_ccgt_ccs": 600.0,
#     "gas_ccgt_hydrogen_10": 400.0,

#     "oil": 500.0,
# }

# Default emission factors (tCO2/MWh_e).
# These are carrier-level values, not fuel-level values.
# For CCS, residual emissions are simplified as 10% of the unabated plant.
# For ammonia/hydrogen co-firing, combustion CO2 is reduced by the co-firing share.
# Upstream emissions are not included here.
EMISSION_FACTOR_TCO2_PER_MWH = {
    "coal": 0.90,
    "coal_ccs": 0.09,
    "coal_ammonia_20": 0.72,
    # Cost WG biomass 5% co-firing is mass-basis. With the heat-share conversion above,
    # residual direct CO2 is roughly coal EF * coal heat share ~= 0.87 tCO2/MWh.
    "coal_biomass_5": 0.87,
    "coal_biomass": 0.87,

    "gas_ccgt": 0.40,
    "gas_ocgt": 0.50,
    "gas_ccgt_ccs": 0.04,
    "gas_ccgt_hydrogen_10": 0.36,
    "hydrogen": 0.0,
    "ammonia": 0.0,

    "oil": 0.70,
    "biomass": 0.0,
}

# Non-fossil variable cost defaults (JPY/MWh).
NUCLEAR_MARGINAL_COST = 20.0
SOLAR_MARGINAL_COST = 0.0
WIND_MARGINAL_COST = 0.0
HYDRO_MARGINAL_COST = 10.0
GEOTHERMAL_MARGINAL_COST = 15.0
BIOMASS_MARGINAL_COST = 80.0

NONFOSSIL_MARGINAL_COST = {
    "nuclear": NUCLEAR_MARGINAL_COST,

    # PV split into utility/residential for Cost WG-style cost assumptions.
    # They can share the same solar_pu_2040.csv time series.
    "solar_utility": SOLAR_MARGINAL_COST,
    "solar_residential": SOLAR_MARGINAL_COST,
    "solar_bipv": SOLAR_MARGINAL_COST,

    # Wind split by onshore / offshore fixed / offshore floating.
    "wind_on": WIND_MARGINAL_COST,
    "wind_off_fx": WIND_MARGINAL_COST,
    "wind_off_fl": WIND_MARGINAL_COST,

    "hydro": HYDRO_MARGINAL_COST,
    "hydro_m": HYDRO_MARGINAL_COST,
    "hydro_s": HYDRO_MARGINAL_COST,
    "geothermal": GEOTHERMAL_MARGINAL_COST,
    "biomass": BIOMASS_MARGINAL_COST,

    # backward compatibility
    "solar": SOLAR_MARGINAL_COST,
    "wind_on": WIND_MARGINAL_COST,
    "wind_off": WIND_MARGINAL_COST,
}

# VRE carriers used for curtailment reporting.
VRE_CARRIERS = {
    "solar_utility",
    "solar_residential",
    "solar_bipv",
    "wind_on",
    "wind_off_fx",
    "wind_off_fl",

    # backward compatibility
    "solar",
    "wind_on",
    "wind_off",
}

# Output grouping for chart files.
PV_OUTPUT_CARRIERS = {"solar_utility", "solar_residential", "solar_bipv", "solar"}
WIND_OUTPUT_CARRIERS = {
    "wind_on",
    "wind_off_fx",
    "wind_off_fl",
    "wind_on",
    "wind_off",
}
THERMAL_OUTPUT_CARRIERS = set(THERMAL_FUEL_MIX.keys())
STORAGE_CARRIERS = {"battery", "phs"}


# Default carrier groups for Energy Basic Plan-style generation mix constraints.
# Users can override these groups by adding a "carriers" column in basic_mix_2040.csv.
BASIC_MIX_DEFAULT_CARRIER_GROUPS = {
    "solar": ["solar_utility", "solar_residential", "solar_bipv", "solar"],
    "pv": ["solar_utility", "solar_residential", "solar_bipv", "solar"],
    "wind": ["wind_on", "wind_off_fx", "wind_off_fl", "wind_off"],
    "onshore_wind": ["wind_on"],
    "offshore_wind": ["wind_off_fx", "wind_off_fl", "wind_off"],
    "hydro": ["hydro", "hydro_m", "hydro_s"],
    "geothermal": ["geothermal"],
    "biomass": ["biomass"],
    "nuclear": ["nuclear"],
    "ccs": ["coal_ccs", "gas_ccgt_ccs"],
    "thermal": sorted(list(THERMAL_CARRIERS)),
    "fossil": [
        "coal", "oil", "gas_ccgt", "gas_ocgt",
        "coal_ccs", "gas_ccgt_ccs",
        "coal_biomass_5", "coal_biomass", "coal_ammonia_20", "gas_ccgt_hydrogen_10",
    ],
}

BASIC_MIX_DEFAULT_CARRIER_GROUPS["renewable"] = sorted(set(
    BASIC_MIX_DEFAULT_CARRIER_GROUPS["solar"]
    + BASIC_MIX_DEFAULT_CARRIER_GROUPS["wind"]
    + BASIC_MIX_DEFAULT_CARRIER_GROUPS["hydro"]
    + BASIC_MIX_DEFAULT_CARRIER_GROUPS["geothermal"]
    + BASIC_MIX_DEFAULT_CARRIER_GROUPS["biomass"]
))
BASIC_MIX_DEFAULT_CARRIER_GROUPS["renewables"] = BASIC_MIX_DEFAULT_CARRIER_GROUPS["renewable"]
BASIC_MIX_DEFAULT_CARRIER_GROUPS["non_fossil"] = sorted(set(
    BASIC_MIX_DEFAULT_CARRIER_GROUPS["renewable"]
    + BASIC_MIX_DEFAULT_CARRIER_GROUPS["nuclear"]
))
BASIC_MIX_DEFAULT_CARRIER_GROUPS["nonfossil"] = BASIC_MIX_DEFAULT_CARRIER_GROUPS["non_fossil"]

# HVDC fallback investment model.
# If USE_HVDC_DISTANCE_BASED_COST=False, technology_cost_2040.csv carrier=HVDC is used.
USE_HVDC_DISTANCE_BASED_COST = True
HVDC_CONVERTER_COST_JPY_PER_MW = 30_000_000
HVDC_CABLE_COST_JPY_PER_MWKM = 300_000
HVDC_LIFETIME_YEARS = 40
HVDC_DISCOUNT_RATE = 0.03

# For capacity expansion, existing interconnectors may use asymmetric p_min_pu
# values to represent current directional limits. Do not apply those asymmetric
# ratios to new HVDC capacity; otherwise a small expansion can create an
# unrealistically huge reverse-direction capacity. New HVDC capacity is treated
# as symmetric by default.
NEW_HVDC_P_MIN_PU = -1.0
# New HVDC links are represented by two one-way Links with equal capacity.
# This avoids negative p_nom_opt problems with p_min_pu=-1 on extendable Links.
NEW_HVDC_PAIRS = []
# =========================================================
# CO2 cap and shadow price settings
# =========================================================
USE_CO2_CAP_CONSTRAINT = False
CO2_CAP_TCO2 = 250_000_000.0

# CO2 intensity constraint.
# Unit is tCO2/MWh-load. Numerically, this is the same as kgCO2/kWh.
# Example:
#   0.04 tCO2/MWh = 0.04 kgCO2/kWh
#
# For policy_2040.csv, use either:
#   co2_intensity_tco2_per_mwh,0.04
# or:
#   co2_intensity_kgco2_per_kwh,0.04
#
# If either parameter is present, the constraint is turned on automatically.
USE_CO2_INTENSITY_CONSTRAINT = False
CO2_INTENSITY_TCO2_PER_MWH = 0.04

# Energy Basic Plan-style generation mix constraints.
# If enabled, constraints are imposed as annual generation shares over annual load:
#   lower_share * annual_load <= annual_generation(category) <= upper_share * annual_load
# This load denominator keeps the constraints linear and easy to interpret.
USE_BASIC_MIX_CONSTRAINT = False
BASIC_MIX_DENOMINATOR = "load"
BASIC_MIX_DF = pd.DataFrame()

EXPORT_SHADOW_PRICES = True
EXPORT_SELECTED_SHADOW_PRICES_ONLY = True

SELECTED_DUAL_CONSTRAINTS = [
    "Bus-nodal_balance",
    "Generator-ext-p_nom-upper",
    "StorageUnit-ext-p_nom-upper",
    "Line-ext-s_nom-upper",
    "Link-ext-p_nom-upper",
    "Policy-co2_cap",
    "Policy-co2_intensity",
]

# ---------------------------------------------------------
# Fallbacks when max is blank
# ---------------------------------------------------------
# For research cases, p_nom_max/s_nom_max should normally be explicitly set.
# These huge defaults are only to avoid crashes during early testing.
P_NOM_MAX_FALLBACK_MULTIPLIER = 100.0
E_NOM_MAX_FALLBACK_MULTIPLIER = 100.0
LINE_MAX_FALLBACK_MULTIPLIER = 100.0

DEFAULT_P_NOM_MAX_BY_CARRIER = {
    "nuclear": 999999999.0,

    "solar_utility": 999999999.0,
    "solar_residential": 999999999.0,
    "solar_bipv": 999999999.0,
    "wind_on": 999999999.0,
    "wind_off_fx": 999999999.0,
    "wind_off_fl": 999999999.0,

    "hydro": 999999999.0,
    "hydro_m": 999999999.0,
    "hydro_s": 999999999.0,
    "geothermal": 999999999.0,
    "biomass": 999999999.0,

    "coal": 999999999.0,
    "coal_ccs": 999999999.0,
    "coal_biomass_5": 999999999.0,
    "coal_biomass": 999999999.0,
    "coal_ammonia_20": 999999999.0,
    
    "gas_ccgt": 999999999.0,
    "gas_ocgt": 999999999.0,
    "hydrogen": 999999999.0,
    "ammonia": 999999999.0,
    "gas_ccgt_ccs": 999999999.0,
    "gas_ccgt_hydrogen_10": 999999999.0,
    
    "oil": 999999999.0,

    "battery": 999999999.0,
    "phs": 999999999.0,

    # backward compatibility
    "solar": 999999999.0,
    "wind_on": 999999999.0,
    "wind_off": 999999999.0,
    "gas_ccgt": 999999999.0,
    "gas_ocgt": 999999999.0,
}

DEFAULT_E_NOM_MAX_BY_CARRIER = {
    "battery": 9_999_999.0,
    "phs": 9_999_999.0,
}

DEFAULT_LINE_S_NOM_MAX = 9_999_999.0


# =========================================================
# 1. Derived settings
# =========================================================
SNAPSHOT_BLOCKS = []
SNAPSHOT_TO_PERIOD = {}
for period_name, start_ts, n_hours in REPRESENTATIVE_PERIODS:
    idx = pd.date_range(start_ts, periods=n_hours, freq=TIME_FREQ)
    SNAPSHOT_BLOCKS.append(idx)
    for ts in idx:
        SNAPSHOT_TO_PERIOD[ts] = period_name

SNAPSHOTS = pd.DatetimeIndex([]).append(SNAPSHOT_BLOCKS)
N_HOURS = len(SNAPSHOTS)
ANNUAL_HOURS = 8760.0
SNAPSHOT_OBJECTIVE_WEIGHT = ANNUAL_HOURS / N_HOURS

RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = os.path.join(RESULTS_ROOT, f"{RUN_TS}_{SCENARIO_NAME}")
CSV_DIR = os.path.join(RUN_DIR, "results_csv")
PLOT_DIR = os.path.join(RUN_DIR, "results_plots")

for d in [CSV_DIR, PLOT_DIR]:
    os.makedirs(d, exist_ok=True)


# =========================================================
# 2. Helper functions
# =========================================================
def map_to_target_fiscal_year(index, target_fy_start_year: int) -> pd.DatetimeIndex:
    """
    Map a fiscal-year index to a target fiscal year.

    Example for target_fy_start_year=2040:
      2024-04-01 -> 2040-04-01
      2024-12-31 -> 2040-12-31
      2025-01-01 -> 2041-01-01
      2025-03-31 -> 2041-03-31
    """
    mapped = []

    for x in index:
        if x.month >= 4:
            mapped.append(x.replace(year=target_fy_start_year))
        else:
            mapped.append(x.replace(year=target_fy_start_year + 1))

    return pd.DatetimeIndex(mapped)
def read_ts_csv(path: str) -> pd.DataFrame:
    """Read a time-series CSV and select representative-period snapshots.

    Expected format:
        index column = timestamp
        columns = regions

    If the input year differs from the model year, the function shifts the
    input year to the model year and retries. This is useful when reusing
    historical profiles for future-year analysis.
    """
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "snapshot"

    if df.index.has_duplicates:
        df = df.groupby(level=0).mean()

    for col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .replace({"": None, "nan": None, "None": None})
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    out = df.reindex(SNAPSHOTS)

    if out.isna().any().any():
        target_year = SNAPSHOTS[0].year
        shifted = df.copy()
        try:
            shifted.index = map_to_target_fiscal_year(
                shifted.index,
                target_fy_start_year=target_year,
            )
            if shifted.index.has_duplicates:
                shifted = shifted.groupby(level=0).mean()
            out = shifted.reindex(SNAPSHOTS)
        except ValueError:
            pass

    if out.isna().any().any():
        n_missing = int(out.isna().sum().sum())
        raise ValueError(f"{path} has {n_missing} missing values for representative snapshots.")

    return out


def read_nonnegative_ts(path: str) -> pd.DataFrame:
    df = read_ts_csv(path)
    if (df < 0).any().any():
        raise ValueError(f"{path} contains negative values.")
    return df


def read_pu_ts(path: str, regions: list[str]) -> pd.DataFrame:
    df = read_ts_csv(path)

    missing_cols = [r for r in regions if r not in df.columns]
    if missing_cols:
        raise ValueError(f"{path} is missing columns: {missing_cols}")

    df = df[regions].copy()

    if ((df < 0) | (df > 1)).any().any():
        raise ValueError(f"{path} contains p.u. outside [0, 1].")

    return df


def read_key_value_csv(path: str, key_col: str, value_col: str) -> dict:
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip()
    return dict(zip(df[key_col].astype(str), df[value_col]))


def annuity(rate: float, n_years: int) -> float:
    if rate == 0:
        return 1.0 / n_years
    return rate / (1.0 - (1.0 + rate) ** (-n_years))


def clean_nonnegative(df: pd.DataFrame, tol: float = 1e-9) -> pd.DataFrame:
    out = df.copy()
    out = out.mask(out.abs() < tol, 0.0)
    out = out.clip(lower=0.0)
    return out


def get_emission_factor_tco2_per_mwh(carrier: str) -> float:
    """Return direct power-sector emission factor for a model carrier."""
    return EMISSION_FACTOR_TCO2_PER_MWH.get(carrier, 0.0)


def get_carbon_cost_jpy_per_mwh(carrier: str) -> float:
    if not USE_CARBON_PRICE:
        return 0.0
    return CARBON_PRICE_JPY_PER_TCO2 * get_emission_factor_tco2_per_mwh(carrier)


def get_fuel_price_jpy_per_mwh_th_by_fuel(fuel: str) -> float:
    """Return fuel price in JPY/MWh_th for a single fuel."""
    if fuel == "oil":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["oil_usd_per_bbl"] / OIL_MMBTU_PER_BBL
    elif fuel == "coal":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["coal_usd_per_t"] / COAL_MMBTU_PER_T
    elif fuel == "gas":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["gas_usd_per_mmbtu"]
    elif fuel == "ammonia":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["ammonia_usd_per_mmbtu"]
    elif fuel == "hydrogen":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["hydrogen_usd_per_mmbtu"]
    elif fuel == "biomass":
        usd_per_mmbtu = FOSSIL_FUEL_PRICE["biomass_usd_per_mmbtu"]
    else:
        raise ValueError(f"Unsupported fuel for price conversion: {fuel}")

    return usd_per_mmbtu * USDJPY / MWH_PER_MMBTU


def get_fuel_price_jpy_per_mwh_th(carrier: str) -> float:
    """Return blended thermal fuel price in JPY/MWh_th for a carrier.

    For co-firing technologies, fuel prices are averaged by fuel heat share.
    Example:
        coal_ammonia_20 = 0.8 * coal_price + 0.2 * ammonia_price
    """
    fuel_mix = THERMAL_FUEL_MIX.get(carrier)
    if fuel_mix is None:
        raise ValueError(f"Unsupported thermal carrier for fuel conversion: {carrier}")

    total_share = sum(fuel_mix.values())
    if abs(total_share - 1.0) > 1e-6:
        raise ValueError(f"Fuel shares for {carrier} do not sum to 1.0: {fuel_mix}")

    return sum(
        share * get_fuel_price_jpy_per_mwh_th_by_fuel(fuel)
        for fuel, share in fuel_mix.items()
    )


def get_thermal_marginal_cost_jpy_per_mwh(
    carrier: str,
    efficiency: float,
    csv_marginal_cost: float,
) -> float:
    """Return thermal marginal cost in JPY/MWh.

    Definition:
        csv_marginal_cost = variable O&M excluding fuel and CO2 cost [JPY/MWh]

    If USE_FUEL_PRICE_BASED_THERMAL_COST=True:
        marginal cost = fuel price / efficiency + variable O&M + CO2 cost

    Otherwise:
        marginal cost = csv_marginal_cost + CO2 cost

    Notes:
        - Fuel cost is calculated from fuel_price_2040.csv and efficiency.
        - Variable O&M should be provided in technology_cost_2040.csv
          or capacity_expansion_2040.csv as marginal_cost.
        - No thermal VOM values are hard-coded here.
    """
    variable_om_cost = 0.0 if pd.isna(csv_marginal_cost) else float(csv_marginal_cost)

    if USE_FUEL_PRICE_BASED_THERMAL_COST and carrier in THERMAL_FUEL_MIX:
        if efficiency <= 0:
            raise ValueError(f"Efficiency must be positive for {carrier}")

        fuel_cost_jpy_per_mwh_th = get_fuel_price_jpy_per_mwh_th(carrier)
        fuel_cost_jpy_per_mwh_e = fuel_cost_jpy_per_mwh_th / efficiency

        return (
            fuel_cost_jpy_per_mwh_e
            + variable_om_cost
            + get_carbon_cost_jpy_per_mwh(carrier)
        )

    return variable_om_cost + get_carbon_cost_jpy_per_mwh(carrier)

def get_hvdc_annualized_capital_cost(distance_km: float) -> float:
    capex_jpy_per_mw = (
        HVDC_CONVERTER_COST_JPY_PER_MW
        + HVDC_CABLE_COST_JPY_PER_MWKM * distance_km
    )
    return capex_jpy_per_mw * annuity(HVDC_DISCOUNT_RATE, HVDC_LIFETIME_YEARS)


def to_numeric_series(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .replace({"": None, "nan": None, "None": None})
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_capacity_row(df: pd.DataFrame, region: str, carrier: str):
    mask = (df["region"] == region) & (df["carrier"] == carrier)
    if not mask.any():
        return None
    return df.loc[mask].iloc[0]


def get_p_nom_total_max(row, carrier: str, existing: float, extendable: int) -> float:
    raw_max = row.get("p_nom_max")
    if pd.notna(raw_max):
        return float(raw_max)

    if extendable == 1:
        if existing > 0:
            return existing * P_NOM_MAX_FALLBACK_MULTIPLIER
        return DEFAULT_P_NOM_MAX_BY_CARRIER.get(carrier, 0.0)

    return existing


def get_e_nom_total_max(row, carrier: str, existing: float, extendable: int) -> float:
    raw_max = row.get("e_nom_max")
    if pd.notna(raw_max):
        return float(raw_max)

    if extendable == 1:
        if existing > 0:
            return existing * E_NOM_MAX_FALLBACK_MULTIPLIER
        return DEFAULT_E_NOM_MAX_BY_CARRIER.get(carrier, 0.0)

    return existing


def get_line_total_max(existing: float, raw_max, extendable_default: bool = True) -> float:
    if pd.notna(raw_max):
        return float(raw_max)

    if extendable_default:
        if existing > 0:
            return existing * LINE_MAX_FALLBACK_MULTIPLIER
        return DEFAULT_LINE_S_NOM_MAX

    return existing


def get_storage_existing_max_hours(row, stype: str) -> float:
    p_existing = float(row["p_nom_existing"]) if pd.notna(row.get("p_nom_existing")) else 0.0
    e_existing = float(row["e_nom_existing"]) if pd.notna(row.get("e_nom_existing")) else 0.0

    if p_existing > 0 and e_existing > 0:
        return max(e_existing / p_existing, 0.1)

    return DEFAULT_STORAGE_MAX_HOURS[stype]


def get_storage_new_max_hours(row, stype: str) -> float:
    p_max = float(row["p_nom_max"]) if pd.notna(row.get("p_nom_max")) else None
    e_max = float(row["e_nom_max"]) if pd.notna(row.get("e_nom_max")) else None

    if p_max is not None and e_max is not None and p_max > 0 and e_max > 0:
        return max(e_max / p_max, 0.1)

    p_existing = float(row["p_nom_existing"]) if pd.notna(row.get("p_nom_existing")) else 0.0
    e_existing = float(row["e_nom_existing"]) if pd.notna(row.get("e_nom_existing")) else 0.0
    if p_existing > 0 and e_existing > 0:
        return max(e_existing / p_existing, 0.1)

    return DEFAULT_STORAGE_MAX_HOURS[stype]


def get_link_flow_series(bus0: str = None, bus1: str = None, carrier: str = None) -> pd.Series:
    cols = []
    for l in n.links.index:
        ok = True
        if bus0 is not None and str(n.links.loc[l, "bus0"]) != bus0:
            ok = False
        if bus1 is not None and str(n.links.loc[l, "bus1"]) != bus1:
            ok = False
        if carrier is not None and str(n.links.loc[l, "carrier"]) != carrier:
            ok = False
        if ok:
            cols.append(l)

    if not cols:
        return pd.Series(0.0, index=n.snapshots)

    return n.links_t.p0[cols].sum(axis=1)


def get_interconnector_flow_series(from_region: str, to_region: str) -> pd.Series:
    total = pd.Series(0.0, index=n.snapshots)

    for line in n.lines.index:
        bus0 = str(n.lines.loc[line, "bus0"])
        bus1 = str(n.lines.loc[line, "bus1"])
        if bus0 == from_region and bus1 == to_region:
            total = total + n.lines_t.p0[line]
        elif bus0 == to_region and bus1 == from_region:
            total = total - n.lines_t.p0[line]

    for link in n.links.index:
        if str(n.links.loc[link, "carrier"]) != "HVDC":
            continue
        bus0 = str(n.links.loc[link, "bus0"])
        bus1 = str(n.links.loc[link, "bus1"])
        if bus0 == from_region and bus1 == to_region:
            total = total + n.links_t.p0[link]
        elif bus0 == to_region and bus1 == from_region:
            total = total - n.links_t.p0[link]

    return total



def get_linopy_var_dim(var, target_index: pd.Index, label: str) -> str:
    """Find the Linopy/xarray dimension whose coordinate contains target_index."""
    target_values = set(target_index.astype(str))

    for dim in var.dims:
        try:
            coord_index = var.coords[dim].to_index().astype(str)
        except Exception:
            continue

        coord_values = set(coord_index)
        if target_values.issubset(coord_values):
            return dim

    raise KeyError(
        f"Could not find dimension for {label}. "
        f"Variable dims: {var.dims}; target sample: {list(target_index[:5])}"
    )


def build_generator_emission_factor_da(network: pypsa.Network, p_var):
    """Build emission-factor DataArray aligned to Generator-p variable dimensions."""
    gen_index = pd.Index(network.generators.index)
    gen_dim = get_linopy_var_dim(p_var, gen_index, "generators")

    gen_coord = p_var.coords[gen_dim].to_index()
    values = [
        get_emission_factor_tco2_per_mwh(str(network.generators.loc[g, "carrier"]))
        if g in network.generators.index
        else 0.0
        for g in gen_coord
    ]

    return xr.DataArray(
        values,
        coords={gen_dim: gen_coord},
        dims=(gen_dim,),
    )


def build_snapshot_weight_da(network: pypsa.Network, p_var, sns):
    """Build snapshot weight DataArray aligned to Generator-p variable dimensions."""
    snapshot_index = pd.Index(sns)
    snap_dim = get_linopy_var_dim(p_var, snapshot_index, "snapshots")

    snap_coord = p_var.coords[snap_dim].to_index()
    weights = network.snapshot_weightings.loc[snap_coord, "objective"].values

    return xr.DataArray(
        weights,
        coords={snap_dim: snap_coord},
        dims=(snap_dim,),
    )


def add_co2_cap_constraint(network: pypsa.Network, sns) -> None:
    """Add annual CO2 emissions cap constraint."""
    if not USE_CO2_CAP_CONSTRAINT:
        return

    m = network.model

    if "Generator-p" not in m.variables:
        raise KeyError("Generator-p variable not found in Linopy model.")

    p = m.variables["Generator-p"]

    emission_factor = build_generator_emission_factor_da(network, p)
    snapshot_weight = build_snapshot_weight_da(network, p, sns)

    annual_emissions = (p * emission_factor * snapshot_weight).sum()

    m.add_constraints(
        annual_emissions <= CO2_CAP_TCO2,
        name="Policy-co2_cap",
    )

def get_annual_load_mwh_from_network(network: pypsa.Network, sns) -> float:
    """Return annualized load in MWh using snapshot objective weights."""
    snapshot_index = pd.Index(sns, name="snapshot")
    weights = network.snapshot_weightings.loc[snapshot_index, "objective"]

    annual_load_mwh = 0.0
    for load_name in network.loads.index:
        annual_load_mwh += (
            network.loads_t.p_set[load_name].loc[snapshot_index] * weights
        ).sum()

    return float(annual_load_mwh)


def add_co2_intensity_constraint(network: pypsa.Network, sns) -> None:
    """Add annual average CO2 intensity constraint.

    Constraint:
        annual_emissions <= CO2_INTENSITY_TCO2_PER_MWH * annual_load_mwh

    Unit:
        CO2_INTENSITY_TCO2_PER_MWH = tCO2/MWh-load
        This is numerically equal to kgCO2/kWh-load.
    """
    if not USE_CO2_INTENSITY_CONSTRAINT:
        return

    m = network.model

    if "Generator-p" not in m.variables:
        raise KeyError("Generator-p variable not found in Linopy model.")

    p = m.variables["Generator-p"]

    emission_factor = build_generator_emission_factor_da(network, p)
    snapshot_weight = build_snapshot_weight_da(network, p, sns)

    annual_emissions = (p * emission_factor * snapshot_weight).sum()
    annual_load_mwh = get_annual_load_mwh_from_network(network, sns)
    co2_cap_from_intensity = CO2_INTENSITY_TCO2_PER_MWH * annual_load_mwh

    print("Adding CO2 intensity constraint:")
    print(f"  annual_load_mwh = {annual_load_mwh:.6f}")
    print(f"  target_intensity_tco2_per_mwh = {CO2_INTENSITY_TCO2_PER_MWH:.6f}")
    print(f"  implied_co2_cap_tco2 = {co2_cap_from_intensity:.6f}")

    m.add_constraints(
        annual_emissions <= co2_cap_from_intensity,
        name="Policy-co2_intensity",
    )

def add_symmetric_hvdc_capacity_constraints(network: pypsa.Network, sns) -> None:
    """Force paired one-way NEW HVDC Links to have the same p_nom capacity.

    New HVDC corridors are represented as two one-way Links:
      - <line>_new_forward: bus0 -> bus1
      - <line>_new_reverse: bus1 -> bus0

    The equality constraint below makes the pair equivalent to one physical
    bidirectional corridor with the same capacity in both directions.
    """
    if not NEW_HVDC_PAIRS:
        return

    m = network.model

    if "Link-p_nom" not in m.variables:
        print("WARNING: Link-p_nom variable not found. Skip symmetric HVDC constraints.")
        return

    link_p_nom = m.variables["Link-p_nom"]

    for corridor_name, forward_name, reverse_name in NEW_HVDC_PAIRS:
        if forward_name not in network.links.index or reverse_name not in network.links.index:
            continue

        # PyPSA/Linopy dimension names can differ slightly by version.
        # Find the dimension whose coordinate contains our Link names.
        link_dim = None
        for dim in link_p_nom.dims:
            try:
                coord_values = set(link_p_nom.coords[dim].to_index())
            except Exception:
                continue
            if forward_name in coord_values and reverse_name in coord_values:
                link_dim = dim
                break

        if link_dim is None:
            raise KeyError(
                "Could not find Link-p_nom dimension containing HVDC pair "
                f"{forward_name}, {reverse_name}. Dims: {link_p_nom.dims}"
            )

        m.add_constraints(
            link_p_nom.loc[{link_dim: forward_name}]
            == link_p_nom.loc[{link_dim: reverse_name}],
            name=f"Policy-symmetric_hvdc_capacity_{corridor_name}",
        )


def add_representative_period_storage_boundary_constraints(network: pypsa.Network, sns) -> None:
    """Prevent storage energy carryover across representative periods.

    PyPSA treats the selected snapshots as one continuous time series.
    For representative weeks, that would let StorageUnits move energy
    from winter to spring, spring to summer, etc. This helper fixes SOC
    to zero at the first and last snapshot of each representative block.

    This is intentionally conservative, but robust and transparent.
    For full8760 cases, this function does nothing; annual cyclic SOC is
    handled by cyclic_state_of_charge=True on each StorageUnit.
    """
    if STORAGE_CYCLIC_SOC:
        return
    if REPRESENTATIVE_STORAGE_BOUNDARY_MODE != "zero":
        return
    if network.storage_units.empty:
        return

    m = network.model

    if "StorageUnit-state_of_charge" not in m.variables:
        print("WARNING: StorageUnit-state_of_charge variable not found. Skip storage boundary constraints.")
        return

    soc = m.variables["StorageUnit-state_of_charge"]

    snapshot_dim = None
    storage_dim = None

    # Find dimension names robustly across PyPSA/Linopy versions.
    first_snapshot = SNAPSHOTS[0]
    first_storage = network.storage_units.index[0]

    for dim in soc.dims:
        try:
            coord_values = set(soc.coords[dim].to_index())
        except Exception:
            continue
        if first_snapshot in coord_values:
            snapshot_dim = dim
        if first_storage in coord_values:
            storage_dim = dim

    if snapshot_dim is None or storage_dim is None:
        raise KeyError(
            "Could not identify StorageUnit-state_of_charge dimensions. "
            f"Dims: {soc.dims}"
        )

    storage_units = list(network.storage_units.index)

    for period_name, start_ts, n_hours in REPRESENTATIVE_PERIODS:
        period_snapshots = pd.date_range(start_ts, periods=n_hours, freq=TIME_FREQ)
        first_ts = period_snapshots[0]
        last_ts = period_snapshots[-1]

        # Both endpoints are fixed to zero to break artificial inter-period
        # energy transfer. This avoids seasonal carryover by short-duration
        # batteries or pumped hydro in representative-week models.
        m.add_constraints(
            soc.loc[{snapshot_dim: first_ts, storage_dim: storage_units}] == 0.0,
            name=f"Policy-storage_soc_start_zero_{period_name}",
        )
        m.add_constraints(
            soc.loc[{snapshot_dim: last_ts, storage_dim: storage_units}] == 0.0,
            name=f"Policy-storage_soc_end_zero_{period_name}",
        )


def safe_constraint_token(value: str) -> str:
    """Return a simple ASCII-ish token for constraint names."""
    token = str(value).strip().lower()
    for old, new in [
        (" ", "_"), ("/", "_"), ("\\", "_"), ("-", "_"),
        (".", "_"), ("(", ""), (")", ""), ("[", ""), ("]", ""),
        ("%", "pct"), ("+", "plus"), ("&", "and"),
    ]:
        token = token.replace(old, new)
    token = "".join(ch for ch in token if ch.isalnum() or ch == "_")
    while "__" in token:
        token = token.replace("__", "_")
    return token.strip("_") or "mix"


def parse_share_value(value) -> float | None:
    """Parse a share value written as fraction (0.20) or percent (20)."""
    if value is None or pd.isna(value):
        return None
    x = float(value)
    if x > 1.0:
        x = x / 100.0
    if x < 0.0:
        raise ValueError(f"Share must be non-negative: {value}")
    return x


def parse_carrier_list(value) -> list[str]:
    """Parse a semicolon/comma/pipe-separated carrier list."""
    if value is None or pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    for sep in ["|", ";"]:
        text = text.replace(sep, ",")
    return [x.strip() for x in text.split(",") if x.strip()]


def get_basic_mix_carriers(row) -> list[str]:
    """Return carriers covered by one basic_mix_2040.csv row."""
    carriers = parse_carrier_list(row.get("carriers") if "carriers" in row.index else None)
    if carriers:
        return carriers

    category = str(row["category"]).strip().lower()
    if category not in BASIC_MIX_DEFAULT_CARRIER_GROUPS:
        raise KeyError(
            f"No default carrier group for basic mix category '{category}'. "
            "Add a carriers column in basic_mix_2040.csv for this row."
        )
    return BASIC_MIX_DEFAULT_CARRIER_GROUPS[category]


def build_generator_group_mask_da(network: pypsa.Network, p_var, carriers: list[str], label: str):
    """Build a 0/1 DataArray aligned to Generator-p, selecting carriers in a group."""
    gen_index = pd.Index(network.generators.index)
    gen_dim = get_linopy_var_dim(p_var, gen_index, f"generators for {label}")

    gen_coord = p_var.coords[gen_dim].to_index()
    carrier_set = set(str(c) for c in carriers)
    values = [
        1.0 if (g in network.generators.index and str(network.generators.loc[g, "carrier"]) in carrier_set) else 0.0
        for g in gen_coord
    ]

    return xr.DataArray(
        values,
        coords={gen_dim: gen_coord},
        dims=(gen_dim,),
    )


def add_basic_mix_constraints(network: pypsa.Network, sns) -> None:
    """Add Energy Basic Plan-style annual generation mix constraints.

    Denominator is annual load, not total generation:
        lower_share * annual_load <= annual_generation(category) <= upper_share * annual_load

    This keeps the RHS constant and makes shadow prices easy to interpret:
      - upper constraint value: cost reduction from allowing 1 more MWh of that category
      - lower constraint value: cost reduction from requiring 1 less MWh of that category
    """
    if not USE_BASIC_MIX_CONSTRAINT:
        return
    if BASIC_MIX_DF.empty:
        raise ValueError("USE_BASIC_MIX_CONSTRAINT=True but BASIC_MIX_DF is empty.")

    m = network.model
    if "Generator-p" not in m.variables:
        raise KeyError("Generator-p variable not found in Linopy model.")

    p = m.variables["Generator-p"]
    snapshot_weight = build_snapshot_weight_da(network, p, sns)
    annual_load_mwh = get_annual_load_mwh_from_network(network, sns)

    print("Adding Energy Basic Plan-style generation mix constraints:")
    print(f"  denominator = annual load")
    print(f"  annual_load_mwh = {annual_load_mwh:.6f}")

    for _, row in BASIC_MIX_DF.iterrows():
        category = str(row["category"]).strip()
        category_token = safe_constraint_token(category)
        carriers = get_basic_mix_carriers(row)

        group_mask = build_generator_group_mask_da(network, p, carriers, category)
        annual_generation = (p * group_mask * snapshot_weight).sum()

        lower_share = None
        upper_share = None
        if "lower_share" in row.index:
            lower_share = parse_share_value(row.get("lower_share"))
        if "upper_share" in row.index:
            upper_share = parse_share_value(row.get("upper_share"))
        if lower_share is None and "lower_pct" in row.index:
            lower_share = parse_share_value(row.get("lower_pct"))
        if upper_share is None and "upper_pct" in row.index:
            upper_share = parse_share_value(row.get("upper_pct"))

        lower_mwh = row.get("lower_mwh") if "lower_mwh" in row.index else None
        upper_mwh = row.get("upper_mwh") if "upper_mwh" in row.index else None

        if lower_share is not None and lower_share > 1.5:
            raise ValueError(f"lower_share seems invalid for {category}: {lower_share}")
        if upper_share is not None and upper_share > 1.5:
            raise ValueError(f"upper_share seems invalid for {category}: {upper_share}")

        if lower_share is not None:
            lower_bound = lower_share * annual_load_mwh
        elif lower_mwh is not None and pd.notna(lower_mwh):
            lower_bound = float(lower_mwh)
        else:
            lower_bound = None

        if upper_share is not None:
            upper_bound = upper_share * annual_load_mwh
        elif upper_mwh is not None and pd.notna(upper_mwh):
            upper_bound = float(upper_mwh)
        else:
            upper_bound = None

        if lower_bound is None and upper_bound is None:
            print(f"  WARNING: {category} has neither lower nor upper bound. Skip.")
            continue
        if lower_bound is not None and upper_bound is not None and lower_bound > upper_bound + 1e-6:
            raise ValueError(
                f"Basic mix lower bound exceeds upper bound for {category}: "
                f"lower={lower_bound}, upper={upper_bound}"
            )

        existing_carriers = sorted(set(network.generators["carrier"].astype(str)))
        missing_from_model = sorted(set(carriers) - set(existing_carriers))
        if missing_from_model:
            print(f"  NOTE: {category} carriers not present in model generators: {missing_from_model}")

        if lower_bound is not None:
            print(
                f"  {category}: lower >= {lower_bound:.3f} MWh "
                f"({(lower_bound / annual_load_mwh * 100.0 if annual_load_mwh else 0):.3f}% of load)"
            )
            m.add_constraints(
                annual_generation >= lower_bound,
                name=f"Policy-basic_mix_{category_token}_lower",
            )

        if upper_bound is not None:
            print(
                f"  {category}: upper <= {upper_bound:.3f} MWh "
                f"({(upper_bound / annual_load_mwh * 100.0 if annual_load_mwh else 0):.3f}% of load)"
            )
            m.add_constraints(
                annual_generation <= upper_bound,
                name=f"Policy-basic_mix_{category_token}_upper",
            )


def add_ce_policy_constraints(network: pypsa.Network, sns) -> None:
    """Add user-defined CE policy constraints before solving."""
    add_symmetric_hvdc_capacity_constraints(network, sns)
    add_representative_period_storage_boundary_constraints(network, sns)
    add_co2_cap_constraint(network, sns)
    add_co2_intensity_constraint(network, sns)
    add_basic_mix_constraints(network, sns)


def dual_dataarray_to_dataframe(da, name: str = "raw_dual") -> pd.DataFrame:
    """Convert a Linopy/xarray dual DataArray to a DataFrame.

    Linopy duals can be either indexed arrays or scalar zero-dimensional
    DataArrays. Annual policy constraints such as Policy-co2_intensity are
    often scalar. xarray.DataArray.to_dataframe() can fail for scalar arrays,
    so handle that case explicitly.
    """
    if getattr(da, "ndim", None) == 0:
        return pd.DataFrame([{name: float(da.item())}])

    return da.to_dataframe(name=name).reset_index()


def export_shadow_prices(network: pypsa.Network, csv_dir: str) -> None:
    """Export shadow prices / dual values from the solved Linopy model."""
    if not EXPORT_SHADOW_PRICES:
        return

    if not hasattr(network, "model") or network.model is None:
        print("WARNING: No Linopy model found. Skip shadow price export.")
        return

    if not hasattr(network.model, "dual"):
        print("WARNING: network.model has no dual attribute. Skip shadow price export.")
        return

    duals = network.model.dual
    if duals is None:
        print("WARNING: model.dual is None. Skip shadow price export.")
        return

    available_constraints = list(duals.data_vars)
    pd.DataFrame({"available_dual_constraint": available_constraints}).to_csv(
        os.path.join(csv_dir, "shadow_price_available_constraints.csv"),
        index=False,
    )

    if EXPORT_SELECTED_SHADOW_PRICES_ONLY:
        target_constraints = [c for c in SELECTED_DUAL_CONSTRAINTS if c in available_constraints]

        # Symmetric HVDC constraints are generated dynamically per corridor.
        # Include them automatically when present.
        target_constraints += [
            c for c in available_constraints
            if (
                c.startswith("Policy-symmetric_hvdc_capacity_")
                or c.startswith("Policy-storage_soc_start_zero_")
                or c.startswith("Policy-storage_soc_end_zero_")
                or c.startswith("Policy-basic_mix_")
            )
            and c not in target_constraints
        ]

        missing_constraints = [c for c in SELECTED_DUAL_CONSTRAINTS if c not in available_constraints]
        if missing_constraints:
            print("WARNING: selected dual constraints not found:")
            for c in missing_constraints:
                print(f"  - {c}")
    else:
        target_constraints = available_constraints

    rows = []

    for cname in target_constraints:
        da = duals[cname]

        try:
            df = dual_dataarray_to_dataframe(da, name="raw_dual")
        except Exception as e:
            print(f"WARNING: failed to convert dual {cname} to dataframe: {e}")
            continue

        df["constraint"] = cname

        scale_divisor = COST_SCALE if COST_SCALE != 0 else 1.0

        if (
            cname.endswith("-upper")
            or cname in {"Policy-co2_cap", "Policy-co2_intensity"}
            or "upper" in cname.lower()
            or "cap" in cname.lower()
        ):
            df["relaxation_value"] = -df["raw_dual"] / scale_divisor
            df["interpretation"] = "positive means relaxing this upper/cap constraint reduces system cost"
        else:
            df["relaxation_value"] = df["raw_dual"] / scale_divisor
            df["interpretation"] = "raw sign; check constraint convention"

        rows.append(df)

        safe_name = cname.replace("/", "_").replace(" ", "_")
        df.to_csv(os.path.join(csv_dir, f"shadow_price_{safe_name}.csv"), index=False)

    if rows:
        all_duals_df = pd.concat(rows, ignore_index=True)
        all_duals_df.to_csv(os.path.join(csv_dir, "shadow_prices_selected_long.csv"), index=False)

        summary_rows = []
        for cname, g in all_duals_df.groupby("constraint"):
            vals = g["relaxation_value"].dropna()
            raw_vals = g["raw_dual"].dropna()
            summary_rows.append({
                "constraint": cname,
                "n_values": len(vals),
                "raw_dual_min": raw_vals.min() if len(raw_vals) else None,
                "raw_dual_mean": raw_vals.mean() if len(raw_vals) else None,
                "raw_dual_max": raw_vals.max() if len(raw_vals) else None,
                "relaxation_value_min": vals.min() if len(vals) else None,
                "relaxation_value_mean": vals.mean() if len(vals) else None,
                "relaxation_value_max": vals.max() if len(vals) else None,
                "nonzero_count_abs_gt_1e-6": int((vals.abs() > 1e-6).sum()) if len(vals) else 0,
            })

        pd.DataFrame(summary_rows).to_csv(os.path.join(csv_dir, "shadow_price_summary.csv"), index=False)

    print("Shadow price export finished.")


def export_co2_shadow_price_summary(network: pypsa.Network, csv_dir: str) -> None:
    """Export CO2 constraint shadow prices in an easy-to-read CSV.

    Sign convention:
      shadow_price_jpy_per_tco2 > 0 means relaxing the corresponding CO2
      constraint by 1 tCO2 reduces annual system cost by that many JPY.

    Notes:
      - Policy-co2_cap is directly an annual CO2 cap in tCO2.
      - Policy-co2_intensity is implemented as:
            annual_emissions <= CO2_INTENSITY_TCO2_PER_MWH * annual_load_mwh
        so its shadow price has the same interpretation as the shadow price of
        the implied annual CO2 cap.
      - If an exogenous carbon price is also included in generator marginal
        costs, this shadow price is the additional value of the binding CO2
        constraint on top of that exogenous carbon price.
    """
    if not hasattr(network, "model") or network.model is None:
        print("WARNING: No Linopy model found. Skip CO2 shadow price export.")
        return

    if not hasattr(network.model, "dual") or network.model.dual is None:
        print("WARNING: model.dual is unavailable. Skip CO2 shadow price export.")
        return

    duals = network.model.dual
    scale_divisor = COST_SCALE if COST_SCALE != 0 else 1.0
    rows = []

    for cname in ["Policy-co2_cap", "Policy-co2_intensity"]:
        if cname not in duals.data_vars:
            continue

        da = duals[cname]

        try:
            if getattr(da, "ndim", None) == 0:
                raw_dual = float(da.item())
            else:
                values = da.values
                if values.size != 1:
                    print(
                        f"WARNING: {cname} has {values.size} dual values; "
                        "using the first value for the CO2 summary."
                    )
                raw_dual = float(values.ravel()[0])
        except Exception as e:
            print(f"WARNING: failed to read dual {cname}: {e}")
            continue

        shadow_price_jpy_per_tco2 = -raw_dual / scale_divisor

        rows.append({
            "constraint": cname,
            "raw_dual": raw_dual,
            "shadow_price_jpy_per_tco2": shadow_price_jpy_per_tco2,
            "shadow_price_jpy_per_kgco2": shadow_price_jpy_per_tco2 / 1000.0,
            "shadow_price_thousand_jpy_per_tco2": shadow_price_jpy_per_tco2 / 1000.0,
            "external_carbon_price_jpy_per_tco2": CARBON_PRICE_JPY_PER_TCO2 if USE_CARBON_PRICE else 0.0,
            "effective_marginal_co2_cost_jpy_per_tco2": (
                shadow_price_jpy_per_tco2
                + (CARBON_PRICE_JPY_PER_TCO2 if USE_CARBON_PRICE else 0.0)
            ),
            "interpretation": (
                "Positive shadow_price_jpy_per_tco2 means relaxing this CO2 "
                "constraint by 1 tCO2 reduces annual system cost by this many JPY. "
                "effective_marginal_co2_cost adds the exogenous carbon price if used."
            ),
        })

    if not rows:
        print("WARNING: No CO2 policy duals found. CO2 shadow price summary was not exported.")
        return

    pd.DataFrame(rows).to_csv(
        os.path.join(csv_dir, "co2_shadow_price_summary.csv"),
        index=False,
    )
    print("CO2 shadow price summary exported.")


def export_basic_mix_shadow_price_summary(network: pypsa.Network, csv_dir: str) -> None:
    """Export shadow prices for Energy Basic Plan-style mix constraints.

    The constraints use annual load as denominator:
        lower_share * annual_load <= annual_generation(category) <= upper_share * annual_load

    relaxation_value_jpy_per_mwh is interpreted as:
      - lower: cost reduction from reducing the required generation by 1 MWh
      - upper: cost reduction from allowing 1 additional MWh

    value_trillion_jpy_per_1pct_load_share converts the same value to the annual
    cost impact of relaxing the share bound by 1 percentage point of annual load.
    """
    if not USE_BASIC_MIX_CONSTRAINT:
        return
    if not hasattr(network, "model") or network.model is None:
        print("WARNING: No Linopy model found. Skip basic mix shadow price export.")
        return
    if not hasattr(network.model, "dual") or network.model.dual is None:
        print("WARNING: model.dual is unavailable. Skip basic mix shadow price export.")
        return

    duals = network.model.dual
    basic_constraints = [c for c in duals.data_vars if c.startswith("Policy-basic_mix_")]
    if not basic_constraints:
        print("WARNING: No basic mix policy duals found. Basic mix shadow price summary was not exported.")
        return

    annual_load_mwh = get_annual_load_mwh_from_network(network, network.snapshots)
    scale_divisor = COST_SCALE if COST_SCALE != 0 else 1.0
    rows = []

    for cname in basic_constraints:
        da = duals[cname]
        try:
            if getattr(da, "ndim", None) == 0:
                raw_dual = float(da.item())
            else:
                values = da.values
                if values.size != 1:
                    print(
                        f"WARNING: {cname} has {values.size} dual values; "
                        "using the first value for the basic mix summary."
                    )
                raw_dual = float(values.ravel()[0])
        except Exception as e:
            print(f"WARNING: failed to read dual {cname}: {e}")
            continue

        if cname.endswith("_upper"):
            bound_type = "upper"
            relaxation_value = -raw_dual / scale_divisor
            interpretation = "Positive value means allowing 1 additional MWh from this category reduces annual system cost."
        elif cname.endswith("_lower"):
            bound_type = "lower"
            relaxation_value = raw_dual / scale_divisor
            interpretation = "Positive value means requiring 1 less MWh from this category reduces annual system cost."
        else:
            bound_type = "unknown"
            relaxation_value = raw_dual / scale_divisor
            interpretation = "Check constraint convention."

        category = cname.replace("Policy-basic_mix_", "")
        if category.endswith("_upper"):
            category = category[:-6]
        if category.endswith("_lower"):
            category = category[:-6]

        value_jpy_per_1pct = relaxation_value * annual_load_mwh * 0.01

        rows.append({
            "constraint": cname,
            "category_token": category,
            "bound_type": bound_type,
            "raw_dual": raw_dual,
            "relaxation_value_jpy_per_mwh": relaxation_value,
            "annual_load_mwh": annual_load_mwh,
            "value_jpy_per_1pct_load_share": value_jpy_per_1pct,
            "value_billion_jpy_per_1pct_load_share": value_jpy_per_1pct / 1e9,
            "value_trillion_jpy_per_1pct_load_share": value_jpy_per_1pct / 1e12,
            "interpretation": interpretation,
        })

    if rows:
        pd.DataFrame(rows).to_csv(
            os.path.join(csv_dir, "basic_mix_shadow_price_summary.csv"),
            index=False,
        )
        print("Basic mix shadow price summary exported.")


# =========================================================
# 3. Read input files
# =========================================================
print("Reading input files...")

capacity_df = pd.read_csv(os.path.join(INPUT_DIR, CAPACITY_FILE))
lines_df = pd.read_csv(os.path.join(INPUT_DIR, LINES_FILE))

capacity_df.columns = capacity_df.columns.str.replace("\ufeff", "", regex=False).str.strip()
lines_df.columns = lines_df.columns.str.replace("\ufeff", "", regex=False).str.strip()

# Remove blank rows / blank Excel columns in lines_expansion_2040.csv.
# This prevents accidental components such as "nan_new".
lines_df = lines_df.loc[:, ~lines_df.columns.str.startswith("Unnamed")]
lines_df = lines_df.dropna(how="all")
required_line_cols = ["name", "bus0", "bus1", "type"]
missing_line_cols = [c for c in required_line_cols if c not in lines_df.columns]
if missing_line_cols:
    raise KeyError(
        "lines file must contain name, bus0, bus1, and type columns. "
        f"Missing columns: {missing_line_cols}; current columns: {lines_df.columns.tolist()}"
    )
lines_df = lines_df[
    lines_df["name"].notna()
    & lines_df["bus0"].notna()
    & lines_df["bus1"].notna()
    & lines_df["type"].notna()
].copy()
for col in required_line_cols:
    lines_df[col] = lines_df[col].astype(str).str.strip()

# Normalize carrier names to string.
capacity_df["carrier"] = capacity_df["carrier"].astype(str).str.strip()
capacity_df["region"] = capacity_df["region"].astype(str).str.strip()

tech_cost_df = (
    pd.read_csv(os.path.join(INPUT_DIR, TECH_COST_FILE))
    if os.path.exists(os.path.join(INPUT_DIR, TECH_COST_FILE))
    else pd.DataFrame()
)

capacity_df = to_numeric_series(
    capacity_df,
    [
        "p_nom_existing", "p_nom_min", "p_nom_max", "capital_cost",
        "e_nom_existing", "e_nom_min", "e_nom_max", "e_capital_cost",
        "p_nom_extendable", "e_nom_extendable",
        "efficiency", "marginal_cost", "p_min_pu", "lfc_pu",
        "efficiency_store", "efficiency_dispatch", "roundtrip_efficiency", "standing_loss",
        "commission_year", "lifetime_years",
    ],
)

for col in ["p_nom_extendable", "e_nom_extendable"]:
    if col in capacity_df.columns:
        capacity_df[col] = capacity_df[col].fillna(0).astype(int)

lines_df = to_numeric_series(
    lines_df,
    [
        "s_nom_existing", "s_nom_max", "x", "r",
        "efficiency", "distance_km", "p_min_pu", "s_nom",
        "capital_cost",
    ],
)

load_df = read_nonnegative_ts(os.path.join(INPUT_DIR, LOAD_FILE))
regions = list(load_df.columns)

solar_pu = read_pu_ts(os.path.join(INPUT_DIR, SOLAR_PU_FILE), regions)
wind_on_pu = read_pu_ts(os.path.join(INPUT_DIR, WIND_ON_PU_FILE), regions)
wind_off_pu = read_pu_ts(os.path.join(INPUT_DIR, WIND_OFF_PU_FILE), regions)
hydro_pu = read_pu_ts(os.path.join(INPUT_DIR, HYDRO_PU_FILE), regions)
geothermal_pu = read_pu_ts(os.path.join(INPUT_DIR, GEOTHERMAL_PU_FILE), regions)
biomass_pu = read_pu_ts(os.path.join(INPUT_DIR, BIOMASS_PU_FILE), regions)
nuclear_pu = read_pu_ts(os.path.join(INPUT_DIR, NUCLEAR_PU_FILE), regions)

# Carrier-to-time-series mapping.
# Cost WG carrier splits share the available p.u. profiles.
PU_BY_CARRIER = {
    "nuclear": nuclear_pu,

    "solar_utility": solar_pu,
    "solar_residential": solar_pu,
    "solar_bipv": solar_pu,

    "wind_on": wind_on_pu,
    "wind_off_fx": wind_off_pu,
    "wind_off_fl": wind_off_pu,

    "hydro": hydro_pu,
    "hydro_m": hydro_pu,
    "hydro_s": hydro_pu,
    "geothermal": geothermal_pu,
    "biomass": biomass_pu,

    # backward compatibility
    "solar": solar_pu,
    "wind_on": wind_on_pu,
    "wind_off": wind_off_pu,
}

# Read fuel price overrides.
# Expected CSV:
#   fuel,price_usd
#   coal,120
#   gas,9
#   oil,80
#   ammonia,25
#   hydrogen,30
fuel_price_override = read_key_value_csv(
    os.path.join(INPUT_DIR, FUEL_PRICE_FILE),
    key_col="fuel",
    value_col="price_usd",
)
if fuel_price_override:
    if "coal" in fuel_price_override:
        FOSSIL_FUEL_PRICE["coal_usd_per_t"] = float(fuel_price_override["coal"])
    if "gas" in fuel_price_override:
        FOSSIL_FUEL_PRICE["gas_usd_per_mmbtu"] = float(fuel_price_override["gas"])
    if "oil" in fuel_price_override:
        FOSSIL_FUEL_PRICE["oil_usd_per_bbl"] = float(fuel_price_override["oil"])
    if "ammonia" in fuel_price_override:
        FOSSIL_FUEL_PRICE["ammonia_usd_per_mmbtu"] = float(fuel_price_override["ammonia"])
    if "hydrogen" in fuel_price_override:
        FOSSIL_FUEL_PRICE["hydrogen_usd_per_mmbtu"] = float(fuel_price_override["hydrogen"])
    if "biomass" in fuel_price_override:
        FOSSIL_FUEL_PRICE["biomass_usd_per_mmbtu"] = float(fuel_price_override["biomass"])

# Read emission-factor overrides.
# Expected CSV:
#   fuel,tco2_per_mwh
# The "fuel" column can contain either a fuel name or a carrier name.
# For carrier-level technologies such as coal_ccs or gas_ccgt_hydrogen_10,
# use the carrier name.
emission_override = read_key_value_csv(
    os.path.join(INPUT_DIR, EMISSION_FACTOR_FILE),
    key_col="fuel",
    value_col="tco2_per_mwh",
)
if emission_override:
    for k, v in emission_override.items():
        EMISSION_FACTOR_TCO2_PER_MWH[str(k)] = float(v)

# Read policy overrides.
policy_override = read_key_value_csv(
    os.path.join(INPUT_DIR, POLICY_FILE),
    key_col="parameter",
    value_col="value",
)
if policy_override:
    if "carbon_price" in policy_override:
        CARBON_PRICE_JPY_PER_TCO2 = float(policy_override["carbon_price"])
    if "co2_cap_tco2" in policy_override:
        CO2_CAP_TCO2 = float(policy_override["co2_cap_tco2"])
    if "use_co2_intensity_constraint" in policy_override:
        USE_CO2_INTENSITY_CONSTRAINT = str(policy_override["use_co2_intensity_constraint"]).strip().lower() in {
            "1", "true", "yes", "y", "on"
        }
    if "co2_intensity_tco2_per_mwh" in policy_override:
        CO2_INTENSITY_TCO2_PER_MWH = float(policy_override["co2_intensity_tco2_per_mwh"])
        USE_CO2_INTENSITY_CONSTRAINT = True
    if "co2_intensity_kgco2_per_kwh" in policy_override:
        # Numerically identical to tCO2/MWh.
        CO2_INTENSITY_TCO2_PER_MWH = float(policy_override["co2_intensity_kgco2_per_kwh"])
        USE_CO2_INTENSITY_CONSTRAINT = True
    if "use_basic_mix_constraint" in policy_override:
        USE_BASIC_MIX_CONSTRAINT = str(policy_override["use_basic_mix_constraint"]).strip().lower() in {
            "1", "true", "yes", "y", "on"
        }
    if "basic_mix_file" in policy_override:
        BASIC_MIX_FILE = str(policy_override["basic_mix_file"]).strip()

print("Policy settings after reading policy_2040.csv:")
print(f"  USE_CARBON_PRICE = {USE_CARBON_PRICE}")
print(f"  CARBON_PRICE_JPY_PER_TCO2 = {CARBON_PRICE_JPY_PER_TCO2}")
print(f"  USE_CO2_CAP_CONSTRAINT = {USE_CO2_CAP_CONSTRAINT}")
print(f"  CO2_CAP_TCO2 = {CO2_CAP_TCO2}")
print(f"  USE_CO2_INTENSITY_CONSTRAINT = {USE_CO2_INTENSITY_CONSTRAINT}")
print(f"  CO2_INTENSITY_TCO2_PER_MWH = {CO2_INTENSITY_TCO2_PER_MWH}")
print(f"  USE_BASIC_MIX_CONSTRAINT = {USE_BASIC_MIX_CONSTRAINT}")
print(f"  BASIC_MIX_DENOMINATOR = {BASIC_MIX_DENOMINATOR}")
print(f"  BASIC_MIX_FILE = {BASIC_MIX_FILE}")

# Read Energy Basic Plan-style generation mix constraints if requested.
# Expected CSV columns:
#   category,lower_share,upper_share,carriers(optional)
# Shares can be written either as fractions (0.20) or percentages (20).
# The optional carriers column is a semicolon/comma/pipe-separated list of model carriers.
# If carriers is omitted, BASIC_MIX_DEFAULT_CARRIER_GROUPS[category] is used.
if USE_BASIC_MIX_CONSTRAINT:
    basic_mix_path = os.path.join(INPUT_DIR, BASIC_MIX_FILE)
    if not os.path.exists(basic_mix_path):
        raise FileNotFoundError(
            f"USE_BASIC_MIX_CONSTRAINT=True but {basic_mix_path} was not found. "
            "Create basic_mix_2040.csv or set basic_mix_file in policy_2040.csv."
        )

    BASIC_MIX_DF = pd.read_csv(basic_mix_path)
    BASIC_MIX_DF.columns = BASIC_MIX_DF.columns.str.replace("\ufeff", "", regex=False).str.strip()

    required_cols = ["category"]
    missing_cols = [c for c in required_cols if c not in BASIC_MIX_DF.columns]
    if missing_cols:
        raise KeyError(f"{BASIC_MIX_FILE} is missing required columns: {missing_cols}")

    for col in ["lower_share", "upper_share", "lower_pct", "upper_pct", "lower_mwh", "upper_mwh"]:
        if col in BASIC_MIX_DF.columns:
            BASIC_MIX_DF = to_numeric_series(BASIC_MIX_DF, [col])

    BASIC_MIX_DF["category"] = BASIC_MIX_DF["category"].astype(str).str.strip()
    print("Basic mix constraints loaded:")
    print(BASIC_MIX_DF.to_string(index=False))

tech_cost_lookup = {}
if not tech_cost_df.empty:
    tech_cost_df.columns = tech_cost_df.columns.str.replace("\ufeff", "", regex=False).str.strip()
    tech_cost_df["carrier"] = tech_cost_df["carrier"].astype(str).str.strip()
    tech_cost_df = to_numeric_series(
        tech_cost_df,
        ["capital_cost", "marginal_cost", "efficiency", "e_capital_cost",
         "efficiency_store", "efficiency_dispatch", "roundtrip_efficiency", "standing_loss"],
    )
    for _, row in tech_cost_df.iterrows():
        carrier = str(row["carrier"])
        tech_cost_lookup[carrier] = {
            "capital_cost": float(row["capital_cost"]) if pd.notna(row.get("capital_cost")) else 0.0,
            "marginal_cost": float(row["marginal_cost"]) if pd.notna(row.get("marginal_cost")) else 0.0,
            "efficiency": float(row["efficiency"]) if pd.notna(row.get("efficiency")) else None,
            "e_capital_cost": float(row["e_capital_cost"]) if pd.notna(row.get("e_capital_cost")) else 0.0,
            "efficiency_store": float(row["efficiency_store"]) if pd.notna(row.get("efficiency_store")) else None,
            "efficiency_dispatch": float(row["efficiency_dispatch"]) if pd.notna(row.get("efficiency_dispatch")) else None,
            "roundtrip_efficiency": float(row["roundtrip_efficiency"]) if pd.notna(row.get("roundtrip_efficiency")) else None,
            "standing_loss": float(row["standing_loss"]) if pd.notna(row.get("standing_loss")) else 0.0,
        }

if "p_nom_extendable" in capacity_df.columns and "p_nom_max" in capacity_df.columns:
    missing_pmax = capacity_df[
        (capacity_df["p_nom_extendable"] == 1) & (capacity_df["p_nom_max"].isna())
    ][["region", "carrier"]]
    if not missing_pmax.empty:
        print("WARNING: p_nom_max is blank for extendable assets:")
        print(missing_pmax.to_string(index=False))
else:
    raise KeyError(
        "capacity file must contain p_nom_extendable and p_nom_max columns. "
        f"Current columns: {capacity_df.columns.tolist()}"
    )

# Warn about carriers that will not be built unless they are storage/thermal/non-fossil.
known_buildable_carriers = set(PU_BY_CARRIER.keys()) | THERMAL_CARRIERS | STORAGE_CARRIERS
unknown_carriers = sorted(set(capacity_df["carrier"]) - known_buildable_carriers)
if unknown_carriers:
    print("WARNING: These carriers are in capacity_expansion_2040.csv but are not recognized as buildable:")
    for c in unknown_carriers:
        print(f"  - {c}")

# Warn if thermal variable O&M is missing.
# For thermal carriers, marginal_cost should mean variable O&M excluding fuel and CO2.
missing_thermal_vom = []

for carrier in sorted(THERMAL_CARRIERS):
    in_capacity = capacity_df[capacity_df["carrier"] == carrier]

    has_capacity_vom = (
        not in_capacity.empty
        and "marginal_cost" in in_capacity.columns
        and in_capacity["marginal_cost"].notna().any()
    )

    has_tech_vom = (
        carrier in tech_cost_lookup
        and tech_cost_lookup[carrier].get("marginal_cost", None) is not None
        and pd.notna(tech_cost_lookup[carrier].get("marginal_cost"))
    )

    if not has_capacity_vom and not has_tech_vom:
        missing_thermal_vom.append(carrier)

if missing_thermal_vom:
    print("WARNING: Thermal carriers have no variable O&M marginal_cost in CSV inputs.")
    print("         marginal_cost should mean variable O&M excluding fuel and CO2 [JPY/MWh].")
    print("         Missing carriers:")
    for c in missing_thermal_vom:
        print(f"           - {c}")

# =========================================================
# 4. Build network
# =========================================================
print("Building CE network...")

n = pypsa.Network()
n.set_snapshots(SNAPSHOTS)

n.snapshot_weightings["objective"] = SNAPSHOT_OBJECTIVE_WEIGHT
if "generators" in n.snapshot_weightings.columns:
    n.snapshot_weightings["generators"] = 1.0
if "stores" in n.snapshot_weightings.columns:
    n.snapshot_weightings["stores"] = 1.0

print(f"Representative snapshots: {N_HOURS} hours")
print(f"Snapshot objective weight: {SNAPSHOT_OBJECTIVE_WEIGHT:.6f}")
print(f"Storage cyclic SOC: {STORAGE_CYCLIC_SOC}")
print(f"Representative storage boundary mode: {REPRESENTATIVE_STORAGE_BOUNDARY_MODE}")

# Register carriers automatically from input data.
carriers = sorted(
    set(capacity_df["carrier"].dropna().astype(str))
    | {"AC", "HVDC", "dr_shift", "load_shedding"}
)

for c in carriers:
    n.add("Carrier", c)

# ---------------------------------------------------------
# Buses and load
# ---------------------------------------------------------
for region in regions:
    n.add("Bus", region, carrier="AC")

    if DR_SHIFT_SHARE > 0:
        n.add("Bus", f"{region}_dr", carrier="dr_shift")

    base_load = load_df[region].copy()
    dr_load = DR_SHIFT_SHARE * base_load
    inflexible_load = base_load - dr_load

    n.add("Load", f"load_{region}", bus=region, p_set=inflexible_load)

    if DR_SHIFT_SHARE > 0:
        n.add("Load", f"load_dr_{region}", bus=f"{region}_dr", p_set=dr_load)

# ---------------------------------------------------------
# Transmission
# ---------------------------------------------------------
for _, row in lines_df.iterrows():
    line_type = str(row["type"]).upper() if pd.notna(row["type"]) else "AC"
    name = str(row["name"])
    bus0 = str(row["bus0"])
    bus1 = str(row["bus1"])

    s_nom_existing = 0.0
    if "s_nom_existing" in row.index and pd.notna(row["s_nom_existing"]):
        s_nom_existing = float(row["s_nom_existing"])
    elif "s_nom" in row.index and pd.notna(row["s_nom"]):
        s_nom_existing = float(row["s_nom"])

    s_nom_total_max = get_line_total_max(
        existing=s_nom_existing,
        raw_max=row["s_nom_max"] if "s_nom_max" in row.index else None,
        extendable_default=True,
    )

    if line_type == "HVDC":
        efficiency = float(row["efficiency"]) if pd.notna(row.get("efficiency")) else 1.0
        distance_km = float(row["distance_km"]) if pd.notna(row.get("distance_km")) else 0.0
        p_min_pu = float(row["p_min_pu"]) if pd.notna(row.get("p_min_pu")) else -1.0

        if s_nom_existing > 0:
            # Existing HVDC is also represented by two one-way Links.
            # This keeps existing and new HVDC formulations consistent.
            #
            # If the input p_min_pu is -1.0, existing capacity is symmetric:
            #   forward = s_nom_existing
            #   reverse = s_nom_existing
            #
            # If the input p_min_pu is, for example, -0.5, reverse capacity is:
            #   reverse = 0.5 * s_nom_existing
            #
            # Existing links are fixed capacity, so no equality constraint is needed.
            existing_forward_name = f"{name}_existing_forward"
            existing_reverse_name = f"{name}_existing_reverse"
            existing_reverse_capacity = max(-p_min_pu * s_nom_existing, 0.0)

            n.add(
                "Link",
                existing_forward_name,
                bus0=bus0,
                bus1=bus1,
                carrier="HVDC",
                p_nom=s_nom_existing,
                efficiency=efficiency,
                p_min_pu=0.0,
                capital_cost=0.0,
            )

            if existing_reverse_capacity > 0:
                n.add(
                    "Link",
                    existing_reverse_name,
                    bus0=bus1,
                    bus1=bus0,
                    carrier="HVDC",
                    p_nom=existing_reverse_capacity,
                    efficiency=efficiency,
                    p_min_pu=0.0,
                    capital_cost=0.0,
                )

        new_max = max(s_nom_total_max - s_nom_existing, 0.0)
        if new_max > 0:
            if "capital_cost" in row.index and pd.notna(row.get("capital_cost")):
                hvdc_capital_cost = float(row["capital_cost"])
            else:
                hvdc_capital_cost = (
                    get_hvdc_annualized_capital_cost(distance_km)
                    if USE_HVDC_DISTANCE_BASED_COST
                    else tech_cost_lookup.get("HVDC", {}).get("capital_cost", 0.0)
                )

            forward_name = f"{name}_new_forward"
            reverse_name = f"{name}_new_reverse"

            # Charge the physical corridor investment cost only once.
            # The equality constraint will force:
            #   p_nom_forward == p_nom_reverse
            #
            # Therefore, the reverse Link is a modeling device for reverse flow
            # and should not add another corridor investment cost.
            forward_capital_cost = hvdc_capital_cost * COST_SCALE * CAPEX_TIME_WEIGHT
            reverse_capital_cost = 0.0

            n.add(
                "Link",
                forward_name,
                bus0=bus0,
                bus1=bus1,
                carrier="HVDC",
                p_nom=0.0,
                p_nom_extendable=True,
                p_nom_min=0.0,
                p_nom_max=new_max,
                efficiency=efficiency,
                p_min_pu=0.0,
                capital_cost=forward_capital_cost,
            )

            n.add(
                "Link",
                reverse_name,
                bus0=bus1,
                bus1=bus0,
                carrier="HVDC",
                p_nom=0.0,
                p_nom_extendable=True,
                p_nom_min=0.0,
                p_nom_max=new_max,
                efficiency=efficiency,
                p_min_pu=0.0,
                capital_cost=reverse_capital_cost,
            )

            NEW_HVDC_PAIRS.append((name, forward_name, reverse_name))
    else:
        x = float(row["x"]) if pd.notna(row.get("x")) else 0.1
        r = float(row["r"]) if pd.notna(row.get("r")) else 0.01

        if s_nom_existing > 0:
            n.add(
                "Line",
                f"{name}_existing",
                bus0=bus0,
                bus1=bus1,
                x=x,
                r=r,
                s_nom=s_nom_existing,
                carrier="AC",
                capital_cost=0.0,
            )

        new_max = max(s_nom_total_max - s_nom_existing, 0.0)
        if new_max > 0:
            if "capital_cost" in row.index and pd.notna(row.get("capital_cost")):
                ac_capital_cost = float(row["capital_cost"])
            else:
                ac_capital_cost = tech_cost_lookup.get("AC", {}).get("capital_cost", 0.0)

            n.add(
                "Line",
                f"{name}_new",
                bus0=bus0,
                bus1=bus1,
                x=x,
                r=r,
                s_nom=0.0,
                s_nom_extendable=True,
                s_nom_max=new_max,
                carrier="AC",
                capital_cost=ac_capital_cost * COST_SCALE * CAPEX_TIME_WEIGHT,
            )

# ---------------------------------------------------------
# Existing and new non-fossil generators
# ---------------------------------------------------------
nonfossil_carriers_in_input = sorted(set(capacity_df["carrier"]) & set(PU_BY_CARRIER.keys()))

for region in regions:
    for carrier in nonfossil_carriers_in_input:
        row = get_capacity_row(capacity_df, region, carrier)
        if row is None:
            continue

        pu = PU_BY_CARRIER[carrier][region]

        p_existing = float(row["p_nom_existing"]) if pd.notna(row.get("p_nom_existing")) else 0.0
        p_extendable = int(row["p_nom_extendable"]) if pd.notna(row.get("p_nom_extendable")) else 0

        p_cap_cost = (
            float(row["capital_cost"])
            if pd.notna(row.get("capital_cost"))
            else tech_cost_lookup.get(carrier, {}).get("capital_cost", 0.0)
        )

        csv_marginal_cost = (
            float(row["marginal_cost"])
            if pd.notna(row.get("marginal_cost"))
            else tech_cost_lookup.get(
                carrier,
                {}
            ).get("marginal_cost", NONFOSSIL_MARGINAL_COST.get(carrier, 0.0))
        )

        marginal_cost = csv_marginal_cost + get_carbon_cost_jpy_per_mwh(carrier)

        p_min_pu = float(row["p_min_pu"]) if pd.notna(row.get("p_min_pu")) else 0.0

        p_max_total = get_p_nom_total_max(
            row=row,
            carrier=carrier,
            existing=p_existing,
            extendable=p_extendable,
        )

        if p_existing > 0:
            kwargs = dict(
                bus=region,
                carrier=carrier,
                p_nom=p_existing,
                marginal_cost=marginal_cost * COST_SCALE,
                capital_cost=0.0,
                p_max_pu=pu,
            )

            if carrier == "nuclear":
                kwargs["p_min_pu"] = p_min_pu

            n.add("Generator", f"{carrier}_existing_{region}", **kwargs)

        new_max = max(p_max_total - p_existing, 0.0)
        if p_extendable == 1 and new_max > 0:
            kwargs = dict(
                bus=region,
                carrier=carrier,
                p_nom=0.0,
                p_nom_extendable=True,
                p_nom_max=new_max,
                marginal_cost=marginal_cost * COST_SCALE,
                capital_cost=p_cap_cost * COST_SCALE * CAPEX_TIME_WEIGHT,
                p_max_pu=pu,
            )

            if carrier == "nuclear":
                kwargs["p_min_pu"] = p_min_pu

            n.add("Generator", f"{carrier}_new_{region}", **kwargs)

# ---------------------------------------------------------
# Thermal generators
# ---------------------------------------------------------
thermal_capacity_df = capacity_df[capacity_df["carrier"].isin(THERMAL_CARRIERS)].copy()

for _, row in thermal_capacity_df.iterrows():
    carrier = str(row["carrier"])
    region = str(row["region"])

    p_existing = float(row["p_nom_existing"]) if pd.notna(row.get("p_nom_existing")) else 0.0
    p_extendable = int(row["p_nom_extendable"]) if pd.notna(row.get("p_nom_extendable")) else 0

    p_max_total = get_p_nom_total_max(
        row=row,
        carrier=carrier,
        existing=p_existing,
        extendable=p_extendable,
    )

    efficiency = (
        float(row["efficiency"])
        if pd.notna(row.get("efficiency"))
        else tech_cost_lookup.get(carrier, {}).get("efficiency", 0.5)
    )

    csv_marginal_cost = (
        float(row["marginal_cost"])
        if pd.notna(row.get("marginal_cost"))
        else tech_cost_lookup.get(carrier, {}).get("marginal_cost", 0.0)
    )

    capital_cost = (
        float(row["capital_cost"])
        if pd.notna(row.get("capital_cost"))
        else tech_cost_lookup.get(carrier, {}).get("capital_cost", 0.0)
    )

    p_min_pu = float(row["p_min_pu"]) if pd.notna(row.get("p_min_pu")) else 0.0

    marginal_cost = get_thermal_marginal_cost_jpy_per_mwh(
        carrier=carrier,
        efficiency=efficiency,
        csv_marginal_cost=csv_marginal_cost,
    )

    if p_existing > 0:
        n.add(
            "Generator",
            f"{carrier}_existing_{region}",
            bus=region,
            carrier=carrier,
            p_nom=p_existing,
            efficiency=efficiency,
            p_min_pu=p_min_pu,
            marginal_cost=marginal_cost * COST_SCALE,
            capital_cost=0.0,
        )

    new_max = max(p_max_total - p_existing, 0.0)
    if p_extendable == 1 and new_max > 0:
        n.add(
            "Generator",
            f"{carrier}_new_{region}",
            bus=region,
            carrier=carrier,
            p_nom=0.0,
            p_nom_extendable=True,
            p_nom_max=new_max,
            efficiency=efficiency,
            p_min_pu=p_min_pu,
            marginal_cost=marginal_cost * COST_SCALE,
            capital_cost=capital_cost * COST_SCALE * CAPEX_TIME_WEIGHT,
        )

# ---------------------------------------------------------
# Storage using StorageUnit
# ---------------------------------------------------------
STORAGE_EFF_STORE_DEFAULT = {
    "battery": BATTERY_CHARGE_EFF,
    "phs": PHS_CHARGE_EFF,
}
STORAGE_EFF_DISPATCH_DEFAULT = {
    "battery": BATTERY_DISCHARGE_EFF,
    "phs": PHS_DISCHARGE_EFF,
}


def get_storage_efficiencies(row, stype: str) -> tuple[float, float, float]:
    """Return storage charge/discharge efficiencies and standing loss.

    Priority:
      1. capacity_expansion_2040.csv row-specific values
      2. technology_cost_2040.csv carrier values
      3. code defaults

    Supported CSV columns:
      - efficiency_store
      - efficiency_dispatch
      - roundtrip_efficiency  (if store/dispatch are absent, sqrt is used for both)
      - standing_loss
    """
    tc = tech_cost_lookup.get(stype, {})

    eff_store = row.get("efficiency_store") if "efficiency_store" in row.index else None
    eff_dispatch = row.get("efficiency_dispatch") if "efficiency_dispatch" in row.index else None
    roundtrip_eff = row.get("roundtrip_efficiency") if "roundtrip_efficiency" in row.index else None
    standing_loss = row.get("standing_loss") if "standing_loss" in row.index else None

    if pd.isna(eff_store):
        eff_store = tc.get("efficiency_store")
    if pd.isna(eff_dispatch):
        eff_dispatch = tc.get("efficiency_dispatch")
    if pd.isna(roundtrip_eff):
        roundtrip_eff = tc.get("roundtrip_efficiency")
    if pd.isna(standing_loss):
        standing_loss = tc.get("standing_loss", 0.0)

    if (eff_store is None or pd.isna(eff_store)) and (eff_dispatch is None or pd.isna(eff_dispatch)) and roundtrip_eff is not None and pd.notna(roundtrip_eff):
        eff_store = float(roundtrip_eff) ** 0.5
        eff_dispatch = float(roundtrip_eff) ** 0.5

    if eff_store is None or pd.isna(eff_store):
        eff_store = STORAGE_EFF_STORE_DEFAULT[stype]
    if eff_dispatch is None or pd.isna(eff_dispatch):
        eff_dispatch = STORAGE_EFF_DISPATCH_DEFAULT[stype]
    if standing_loss is None or pd.isna(standing_loss):
        standing_loss = 0.0

    eff_store = float(eff_store)
    eff_dispatch = float(eff_dispatch)
    standing_loss = float(standing_loss)

    if not (0 < eff_store <= 1):
        raise ValueError(f"Invalid efficiency_store for {stype}: {eff_store}")
    if not (0 < eff_dispatch <= 1):
        raise ValueError(f"Invalid efficiency_dispatch for {stype}: {eff_dispatch}")
    if not (0 <= standing_loss < 1):
        raise ValueError(f"Invalid standing_loss for {stype}: {standing_loss}")

    return eff_store, eff_dispatch, standing_loss

for region in regions:
    for stype in ["battery", "phs"]:
        row = get_capacity_row(capacity_df, region, stype)
        if row is None:
            continue

        p_existing = float(row["p_nom_existing"]) if pd.notna(row.get("p_nom_existing")) else 0.0
        e_existing = float(row["e_nom_existing"]) if pd.notna(row.get("e_nom_existing")) else 0.0
        p_extendable = int(row["p_nom_extendable"]) if pd.notna(row.get("p_nom_extendable")) else 0

        p_cap_cost = (
            float(row["capital_cost"])
            if pd.notna(row.get("capital_cost"))
            else tech_cost_lookup.get(stype, {}).get("capital_cost", 0.0)
        )
        e_cap_cost = (
            float(row["e_capital_cost"])
            if pd.notna(row.get("e_capital_cost"))
            else tech_cost_lookup.get(stype, {}).get("e_capital_cost", 0.0)
        )

        eff_store, eff_dispatch, standing_loss = get_storage_efficiencies(row, stype)

        p_max_total = get_p_nom_total_max(
            row=row,
            carrier=stype,
            existing=p_existing,
            extendable=p_extendable,
        )

        existing_max_hours = get_storage_existing_max_hours(row, stype)

        if p_existing > 0:
            n.add(
                "StorageUnit",
                f"{stype}_existing_{region}",
                bus=region,
                carrier=stype,
                p_nom=p_existing,
                max_hours=existing_max_hours,
                efficiency_store=eff_store,
                efficiency_dispatch=eff_dispatch,
                cyclic_state_of_charge=STORAGE_CYCLIC_SOC,
                standing_loss=standing_loss,
                marginal_cost=0.0,
                capital_cost=0.0,
            )

        new_max_hours = get_storage_new_max_hours(row, stype)

        e_extendable = int(row["e_nom_extendable"]) if pd.notna(row.get("e_nom_extendable")) else 0
        e_max_total = get_e_nom_total_max(
            row=row,
            carrier=stype,
            existing=e_existing,
            extendable=e_extendable,
        )
        if new_max_hours > 0 and e_max_total > 0:
            p_max_from_e = e_max_total / new_max_hours
            p_max_total = min(p_max_total, p_max_from_e)

        new_max = max(p_max_total - p_existing, 0.0)
        if p_extendable == 1 and new_max > 0:
            annualized_power_cost = p_cap_cost
            annualized_energy_cost_per_mw = e_cap_cost * new_max_hours
            total_capital_cost = annualized_power_cost + annualized_energy_cost_per_mw

            n.add(
                "StorageUnit",
                f"{stype}_new_{region}",
                bus=region,
                carrier=stype,
                p_nom=0.0,
                p_nom_extendable=True,
                p_nom_max=new_max,
                max_hours=new_max_hours,
                efficiency_store=eff_store,
                efficiency_dispatch=eff_dispatch,
                cyclic_state_of_charge=STORAGE_CYCLIC_SOC,
                standing_loss=standing_loss,
                marginal_cost=0.0,
                capital_cost=total_capital_cost * COST_SCALE * CAPEX_TIME_WEIGHT,
            )

# ---------------------------------------------------------
# Load shedding
# ---------------------------------------------------------
for region in regions:
    n.add(
        "Generator",
        f"load_shedding_{region}",
        bus=region,
        carrier="load_shedding",
        p_nom=1e6,
        marginal_cost=LOAD_SHEDDING_COST * COST_SCALE,
        capital_cost=0.0,
    )


# =========================================================
# 5. Solve
# =========================================================
print("Start CE optimize...")

status = n.optimize(
    solver_name=SOLVER_NAME,
    include_objective_constant=True,
    extra_functionality=add_ce_policy_constraints,
    solver_options={
        "presolve": "on",
        "solver": "ipm",
        "user_objective_scale": -7,
        "user_bound_scale": -4,
        "time_limit": 142000,
        "parallel": "on",
    },
)

print("Finish CE optimize.")
print("Status:", status)
print("Objective:", n.objective)
status_text = str(status).lower()

if "optimal" not in status_text:
    raise RuntimeError(
        f"Optimization did not finish as optimal. Status: {status}"
    )
# =========================================================
# 5.5 Export shadow prices / dual values
# =========================================================
export_shadow_prices(n, CSV_DIR)
export_co2_shadow_price_summary(n, CSV_DIR)
export_basic_mix_shadow_price_summary(n, CSV_DIR)


# =========================================================
# 6. Result tables
# =========================================================
print("Building result tables...")

gen_dispatch = clean_nonnegative(n.generators_t.p.copy())
gen_dispatch.index.name = "snapshot"

weight = n.snapshot_weightings["objective"]

build_rows = []

for g in n.generators.index:
    p_nom_initial = float(n.generators.loc[g, "p_nom"]) if pd.notna(n.generators.loc[g, "p_nom"]) else 0.0
    p_nom_opt = (
        float(n.generators.loc[g, "p_nom_opt"])
        if "p_nom_opt" in n.generators.columns and pd.notna(n.generators.loc[g, "p_nom_opt"])
        else p_nom_initial
    )
    build_rows.append({
        "component": "Generator",
        "name": g,
        "carrier": n.generators.loc[g, "carrier"],
        "bus": n.generators.loc[g, "bus"],
        "p_nom_initial": p_nom_initial,
        "p_nom_opt": p_nom_opt,
        "new_build_mw": max(p_nom_opt - p_nom_initial, 0.0),
    })

for l in n.links.index:
    p_nom_initial = float(n.links.loc[l, "p_nom"]) if pd.notna(n.links.loc[l, "p_nom"]) else 0.0
    p_nom_opt = (
        float(n.links.loc[l, "p_nom_opt"])
        if "p_nom_opt" in n.links.columns and pd.notna(n.links.loc[l, "p_nom_opt"])
        else p_nom_initial
    )

    link_name = str(l)
    link_carrier = str(n.links.loc[l, "carrier"])
    raw_new_build_mw = max(p_nom_opt - p_nom_initial, 0.0)

    # For paired NEW HVDC corridors, the reverse Link is only a modeling device.
    # Reporting it as an additional physical build double-counts corridor capacity.
    # Keep raw_new_build_mw for debugging, and use physical_new_build_mw for summaries.
    is_hvdc_new_forward = link_carrier == "HVDC" and link_name.endswith("_new_forward")
    is_hvdc_new_reverse = link_carrier == "HVDC" and link_name.endswith("_new_reverse")

    if is_hvdc_new_reverse:
        physical_new_build_mw = 0.0
        reporting_note = "model reverse Link; physical corridor capacity counted on matching _new_forward row"
    else:
        physical_new_build_mw = raw_new_build_mw
        reporting_note = ""

    build_rows.append({
        "component": "Link",
        "name": l,
        "carrier": n.links.loc[l, "carrier"],
        "bus": f"{n.links.loc[l, 'bus0']}->{n.links.loc[l, 'bus1']}",
        "p_nom_initial": p_nom_initial,
        "p_nom_opt": p_nom_opt,
        "new_build_mw": raw_new_build_mw,
        "physical_new_build_mw": physical_new_build_mw,
        "is_hvdc_new_forward": is_hvdc_new_forward,
        "is_hvdc_new_reverse": is_hvdc_new_reverse,
        "reporting_note": reporting_note,
    })

for line in n.lines.index:
    s_nom_initial = float(n.lines.loc[line, "s_nom"]) if pd.notna(n.lines.loc[line, "s_nom"]) else 0.0
    s_nom_opt = (
        float(n.lines.loc[line, "s_nom_opt"])
        if "s_nom_opt" in n.lines.columns and pd.notna(n.lines.loc[line, "s_nom_opt"])
        else s_nom_initial
    )
    build_rows.append({
        "component": "Line",
        "name": line,
        "carrier": n.lines.loc[line, "carrier"],
        "bus": f"{n.lines.loc[line, 'bus0']}->{n.lines.loc[line, 'bus1']}",
        "s_nom_initial": s_nom_initial,
        "s_nom_opt": s_nom_opt,
        "new_build_mw": max(s_nom_opt - s_nom_initial, 0.0),
    })

for su in n.storage_units.index:
    p_nom_initial = float(n.storage_units.loc[su, "p_nom"]) if pd.notna(n.storage_units.loc[su, "p_nom"]) else 0.0
    p_nom_opt = (
        float(n.storage_units.loc[su, "p_nom_opt"])
        if "p_nom_opt" in n.storage_units.columns and pd.notna(n.storage_units.loc[su, "p_nom_opt"])
        else p_nom_initial
    )
    max_hours = float(n.storage_units.loc[su, "max_hours"]) if pd.notna(n.storage_units.loc[su, "max_hours"]) else 0.0

    build_rows.append({
        "component": "StorageUnit",
        "name": su,
        "carrier": n.storage_units.loc[su, "carrier"],
        "bus": n.storage_units.loc[su, "bus"],
        "p_nom_initial": p_nom_initial,
        "p_nom_opt": p_nom_opt,
        "new_build_mw": max(p_nom_opt - p_nom_initial, 0.0),
        "max_hours": max_hours,
        "new_build_mwh": max((p_nom_opt - p_nom_initial) * max_hours, 0.0),
    })

build_df = pd.DataFrame(build_rows)

# Add reporting columns for non-Link rows and remove tiny numerical noise.
if "physical_new_build_mw" not in build_df.columns:
    build_df["physical_new_build_mw"] = build_df["new_build_mw"]
else:
    build_df["physical_new_build_mw"] = build_df["physical_new_build_mw"].fillna(build_df["new_build_mw"])

for flag_col in ["is_hvdc_new_forward", "is_hvdc_new_reverse"]:
    if flag_col not in build_df.columns:
        build_df[flag_col] = False
    else:
        build_df[flag_col] = build_df[flag_col].fillna(False).astype(bool)

if "reporting_note" not in build_df.columns:
    build_df["reporting_note"] = ""
else:
    build_df["reporting_note"] = build_df["reporting_note"].fillna("")

for num_col in ["new_build_mw", "physical_new_build_mw", "p_nom_opt", "p_nom_initial", "s_nom_opt", "s_nom_initial", "new_build_mwh"]:
    if num_col in build_df.columns:
        build_df.loc[build_df[num_col].abs() < 1e-6, num_col] = 0.0

physical_build_summary_df = (
    build_df.groupby(["component", "carrier"], as_index=False)
    .agg(
        raw_new_build_mw=("new_build_mw", "sum"),
        physical_new_build_mw=("physical_new_build_mw", "sum"),
        new_build_mwh=("new_build_mwh", "sum"),
    )
)

# Corridor-level HVDC capacity summary for physical interpretation.
hvdc_capacity_rows = []
for corridor_name, forward_name, reverse_name in NEW_HVDC_PAIRS:
    if forward_name not in n.links.index or reverse_name not in n.links.index:
        continue

    forward_opt = (
        float(n.links.loc[forward_name, "p_nom_opt"])
        if "p_nom_opt" in n.links.columns and pd.notna(n.links.loc[forward_name, "p_nom_opt"])
        else float(n.links.loc[forward_name, "p_nom"])
    )
    reverse_opt = (
        float(n.links.loc[reverse_name, "p_nom_opt"])
        if "p_nom_opt" in n.links.columns and pd.notna(n.links.loc[reverse_name, "p_nom_opt"])
        else float(n.links.loc[reverse_name, "p_nom"])
    )

    existing_forward_name = f"{corridor_name}_existing_forward"
    existing_reverse_name = f"{corridor_name}_existing_reverse"

    existing_forward_capacity = (
        float(n.links.loc[existing_forward_name, "p_nom"])
        if existing_forward_name in n.links.index and pd.notna(n.links.loc[existing_forward_name, "p_nom"])
        else 0.0
    )
    existing_reverse_capacity = (
        float(n.links.loc[existing_reverse_name, "p_nom"])
        if existing_reverse_name in n.links.index and pd.notna(n.links.loc[existing_reverse_name, "p_nom"])
        else 0.0
    )

    # For a physical corridor summary, report the forward-side capacity.
    # Reverse capacity is kept separately because existing corridors may have
    # asymmetric directional limits in the input data.
    existing_capacity = existing_forward_capacity

    hvdc_capacity_rows.append({
        "corridor": corridor_name,
        "existing_forward_capacity_mw": existing_forward_capacity,
        "existing_reverse_capacity_mw": existing_reverse_capacity,
        "existing_capacity_mw_single_link_basis": existing_capacity,
        "new_forward_link": forward_name,
        "new_reverse_link": reverse_name,
        "new_forward_mw": forward_opt,
        "new_reverse_mw": reverse_opt,
        "physical_new_capacity_mw": forward_opt,
        "new_capacity_gap_forward_minus_reverse_mw": forward_opt - reverse_opt,
        "total_physical_forward_capacity_mw": existing_forward_capacity + forward_opt,
        "total_physical_reverse_capacity_mw": existing_reverse_capacity + reverse_opt,
        "total_physical_capacity_mw": existing_capacity + forward_opt,
        "forward_capital_cost_jpy_per_mw_year": float(n.links.loc[forward_name, "capital_cost"]),
        "reverse_capital_cost_jpy_per_mw_year": float(n.links.loc[reverse_name, "capital_cost"]),
    })

hvdc_capacity_summary_df = pd.DataFrame(hvdc_capacity_rows)

gen_summary_rows = []
for g in n.generators.index:
    gen_summary_rows.append({
        "name": g,
        "carrier": n.generators.loc[g, "carrier"],
        "bus": n.generators.loc[g, "bus"],
        "generation_mwh": (gen_dispatch[g] * weight).sum(),
    })

generation_summary_df = pd.DataFrame(gen_summary_rows)
generation_summary_df = (
    generation_summary_df.groupby("carrier", as_index=False)["generation_mwh"]
    .sum()
    .sort_values("generation_mwh", ascending=False)
)

# Actual generation mix against annual load, for checking Basic Plan-style constraints.
basic_mix_actual_summary_rows = []
if USE_BASIC_MIX_CONSTRAINT and not BASIC_MIX_DF.empty:
    annual_load_mwh_for_mix = get_annual_load_mwh_from_network(n, n.snapshots)
    generation_by_carrier = generation_summary_df.set_index("carrier")["generation_mwh"].to_dict()

    for _, row in BASIC_MIX_DF.iterrows():
        category = str(row["category"]).strip()
        carriers = get_basic_mix_carriers(row)
        actual_generation_mwh = sum(float(generation_by_carrier.get(c, 0.0)) for c in carriers)

        lower_share = parse_share_value(row.get("lower_share")) if "lower_share" in row.index else None
        upper_share = parse_share_value(row.get("upper_share")) if "upper_share" in row.index else None
        if lower_share is None and "lower_pct" in row.index:
            lower_share = parse_share_value(row.get("lower_pct"))
        if upper_share is None and "upper_pct" in row.index:
            upper_share = parse_share_value(row.get("upper_pct"))

        lower_mwh = lower_share * annual_load_mwh_for_mix if lower_share is not None else None
        upper_mwh = upper_share * annual_load_mwh_for_mix if upper_share is not None else None
        actual_share_of_load = actual_generation_mwh / annual_load_mwh_for_mix if annual_load_mwh_for_mix > 0 else None

        basic_mix_actual_summary_rows.append({
            "category": category,
            "carriers": ";".join(carriers),
            "actual_generation_mwh": actual_generation_mwh,
            "annual_load_mwh": annual_load_mwh_for_mix,
            "actual_share_of_load": actual_share_of_load,
            "actual_share_of_load_pct": actual_share_of_load * 100.0 if actual_share_of_load is not None else None,
            "lower_share": lower_share,
            "upper_share": upper_share,
            "lower_bound_mwh": lower_mwh,
            "upper_bound_mwh": upper_mwh,
            "slack_to_lower_mwh": actual_generation_mwh - lower_mwh if lower_mwh is not None else None,
            "slack_to_upper_mwh": upper_mwh - actual_generation_mwh if upper_mwh is not None else None,
        })

basic_mix_actual_summary_df = pd.DataFrame(basic_mix_actual_summary_rows)

curtailment_rows = []
for g in n.generators.index:
    carrier = n.generators.loc[g, "carrier"]
    if carrier not in VRE_CARRIERS:
        continue
    if g not in n.generators_t.p_max_pu.columns:
        continue

    potential = n.generators.loc[g, "p_nom_opt"] * n.generators_t.p_max_pu[g]
    actual = n.generators_t.p[g].clip(lower=0.0)
    curtailment_rows.append({
        "name": g,
        "carrier": carrier,
        "bus": n.generators.loc[g, "bus"],
        "curtailment_mwh": ((potential - actual).clip(lower=0.0) * weight).sum(),
    })

curtailment_df = pd.DataFrame(curtailment_rows)
if not curtailment_df.empty:
    curtailment_df = curtailment_df.sort_values("curtailment_mwh", ascending=False)


# =========================================================
# Nuclear curtailment / unused available nuclear generation
# =========================================================
nuclear_curtailment_rows = []

for g in n.generators.index:
    carrier = str(n.generators.loc[g, "carrier"])
    if carrier != "nuclear":
        continue

    if g not in n.generators_t.p_max_pu.columns:
        continue

    p_nom_opt = (
        float(n.generators.loc[g, "p_nom_opt"])
        if "p_nom_opt" in n.generators.columns and pd.notna(n.generators.loc[g, "p_nom_opt"])
        else float(n.generators.loc[g, "p_nom"])
    )

    potential = p_nom_opt * n.generators_t.p_max_pu[g]
    actual = n.generators_t.p[g].clip(lower=0.0)

    unused = (potential - actual).clip(lower=0.0)

    potential_mwh = (potential * weight).sum()
    actual_mwh = (actual * weight).sum()
    unused_mwh = (unused * weight).sum()

    nuclear_curtailment_rows.append({
        "name": g,
        "carrier": carrier,
        "bus": n.generators.loc[g, "bus"],
        "capacity_mw": p_nom_opt,
        "potential_mwh": potential_mwh,
        "generation_mwh": actual_mwh,
        "nuclear_curtailment_mwh": unused_mwh,
        "curtailment_rate": unused_mwh / potential_mwh if potential_mwh > 0 else None,
        "capacity_factor_actual": actual_mwh / (p_nom_opt * 8760.0) if p_nom_opt > 0 else None,
        "capacity_factor_available": potential_mwh / (p_nom_opt * 8760.0) if p_nom_opt > 0 else None,
    })

nuclear_curtailment_df = pd.DataFrame(nuclear_curtailment_rows)

if not nuclear_curtailment_df.empty:
    nuclear_curtailment_df = nuclear_curtailment_df.sort_values(
        "nuclear_curtailment_mwh",
        ascending=False,
    )

emission_rows = []
for g in n.generators.index:
    carrier = n.generators.loc[g, "carrier"]
    ef = get_emission_factor_tco2_per_mwh(carrier)
    if ef == 0.0:
        continue
    emission_rows.append({
        "name": g,
        "carrier": carrier,
        "bus": n.generators.loc[g, "bus"],
        "emissions_tco2": (gen_dispatch[g] * weight).sum() * ef,
    })

emissions_df = pd.DataFrame(emission_rows)
if not emissions_df.empty:
    emissions_df = emissions_df.sort_values("emissions_tco2", ascending=False)

line_flow_df = n.lines_t.p0.copy() if not n.lines.empty else pd.DataFrame(index=n.snapshots)
hvdc_cols = [c for c in n.links.index if n.links.loc[c, "carrier"] == "HVDC"]
hvdc_flow_df = n.links_t.p0[hvdc_cols].copy() if hvdc_cols else pd.DataFrame(index=n.snapshots)
bus_price_df = (
    n.buses_t.marginal_price.copy()
    if hasattr(n.buses_t, "marginal_price")
    else pd.DataFrame(index=n.snapshots)
)

storage_dispatch_df = n.storage_units_t.p.copy() if not n.storage_units.empty else pd.DataFrame(index=n.snapshots)
storage_soc_df = (
    n.storage_units_t.state_of_charge.copy()
    if (not n.storage_units.empty and hasattr(n.storage_units_t, "state_of_charge"))
    else pd.DataFrame(index=n.snapshots)
)

storage_soc_boundary_rows = []
if not storage_soc_df.empty:
    for period_name, start_ts, n_hours in REPRESENTATIVE_PERIODS:
        period_snapshots = pd.date_range(start_ts, periods=n_hours, freq=TIME_FREQ)
        first_ts = period_snapshots[0]
        last_ts = period_snapshots[-1]
        if first_ts in storage_soc_df.index and last_ts in storage_soc_df.index:
            for su in storage_soc_df.columns:
                start_soc = float(storage_soc_df.loc[first_ts, su])
                end_soc = float(storage_soc_df.loc[last_ts, su])
                storage_soc_boundary_rows.append({
                    "representative_period": period_name,
                    "storage_unit": su,
                    "start_snapshot": first_ts,
                    "end_snapshot": last_ts,
                    "start_soc_mwh": start_soc,
                    "end_soc_mwh": end_soc,
                    "end_minus_start_mwh": end_soc - start_soc,
                    "max_abs_boundary_soc_mwh": max(abs(start_soc), abs(end_soc)),
                })

storage_soc_boundary_df = pd.DataFrame(storage_soc_boundary_rows)


# =========================================================
# 6.x Cost summary
# =========================================================
annual_co2_emissions_tco2 = 0.0
carbon_cost_total = 0.0

for g in n.generators.index:
    carrier = n.generators.loc[g, "carrier"]
    ef = get_emission_factor_tco2_per_mwh(carrier)

    if ef == 0.0:
        continue

    gen_emissions = (gen_dispatch[g] * ef * weight).sum()
    annual_co2_emissions_tco2 += gen_emissions

    carbon_cost_per_mwh = get_carbon_cost_jpy_per_mwh(carrier)
    carbon_cost_total += (gen_dispatch[g] * carbon_cost_per_mwh * weight).sum()

# Investment costs
gen_investment_cost = (
    n.generators["capital_cost"] * n.generators["p_nom_opt"]
).sum()

storage_investment_cost = (
    n.storage_units["capital_cost"] * n.storage_units["p_nom_opt"]
).sum() if not n.storage_units.empty else 0.0

link_investment_cost = (
    n.links["capital_cost"] * n.links["p_nom_opt"]
).sum() if not n.links.empty else 0.0

line_investment_cost = (
    n.lines["capital_cost"] * n.lines["s_nom_opt"]
).sum() if not n.lines.empty else 0.0

# Variable costs, annualized by snapshot weights.
gen_variable_cost = (
    gen_dispatch
    .multiply(n.generators["marginal_cost"], axis=1)
    .multiply(weight, axis=0)
).sum().sum()

storage_variable_cost = 0.0
if not n.storage_units.empty:
    storage_dispatch_for_cost = n.storage_units_t.p.clip(lower=0.0)
    storage_variable_cost = (
        storage_dispatch_for_cost
        .multiply(n.storage_units["marginal_cost"], axis=1)
        .multiply(weight, axis=0)
    ).sum().sum()

total_investment_cost = (
    gen_investment_cost
    + storage_investment_cost
    + link_investment_cost
    + line_investment_cost
)

total_variable_cost = gen_variable_cost + storage_variable_cost
total_system_cost = total_investment_cost + total_variable_cost

annual_load_mwh_for_summary = (
    load_df.multiply(weight, axis=0).sum().sum()
)
actual_co2_intensity_tco2_per_mwh = (
    annual_co2_emissions_tco2 / annual_load_mwh_for_summary
    if annual_load_mwh_for_summary > 0
    else None
)
co2_cap_from_intensity_tco2 = (
    CO2_INTENSITY_TCO2_PER_MWH * annual_load_mwh_for_summary
    if USE_CO2_INTENSITY_CONSTRAINT
    else None
)

cost_summary_df = pd.DataFrame([
    {
        "category": "generator_investment_cost",
        "value": gen_investment_cost,
        "unit": "JPY",
        "note": "Annualized investment cost for generators.",
    },
    {
        "category": "storage_investment_cost",
        "value": storage_investment_cost,
        "unit": "JPY",
        "note": "Annualized investment cost for storage units.",
    },
    {
        "category": "link_investment_cost",
        "value": link_investment_cost,
        "unit": "JPY",
        "note": "Annualized investment cost for links such as HVDC.",
    },
    {
        "category": "line_investment_cost",
        "value": line_investment_cost,
        "unit": "JPY",
        "note": "Annualized investment cost for AC lines.",
    },
    {
        "category": "total_investment_cost",
        "value": total_investment_cost,
        "unit": "JPY",
        "note": "Sum of generator, storage, link, and line investment costs.",
    },
    {
        "category": "generator_variable_cost_including_carbon",
        "value": gen_variable_cost,
        "unit": "JPY",
        "note": "Annualized generator dispatch cost. Includes carbon cost if USE_CARBON_PRICE=True.",
    },
    {
        "category": "storage_variable_cost",
        "value": storage_variable_cost,
        "unit": "JPY",
        "note": "Annualized storage dispatch cost.",
    },
    {
        "category": "carbon_cost_included_in_generator_variable_cost",
        "value": carbon_cost_total,
        "unit": "JPY",
        "note": "Carbon cost component already included in generator_variable_cost_including_carbon. Do not add again.",
    },
    {
        "category": "total_variable_cost_including_carbon",
        "value": total_variable_cost,
        "unit": "JPY",
        "note": "Sum of generator and storage variable costs. Carbon cost is already included if USE_CARBON_PRICE=True.",
    },
    {
        "category": "total_system_cost_including_carbon",
        "value": total_system_cost,
        "unit": "JPY",
        "note": "Total investment plus variable cost. Carbon cost is already included if USE_CARBON_PRICE=True.",
    },
    {
        "category": "annual_co2_emissions",
        "value": annual_co2_emissions_tco2,
        "unit": "tCO2",
        "note": "Annualized CO2 emissions using snapshot objective weights.",
    },
    {
        "category": "annual_load_mwh",
        "value": annual_load_mwh_for_summary,
        "unit": "MWh",
        "note": "Annualized load using snapshot objective weights.",
    },
    {
        "category": "actual_co2_intensity",
        "value": actual_co2_intensity_tco2_per_mwh,
        "unit": "tCO2/MWh_load",
        "note": "Numerically equal to kgCO2/kWh_load.",
    },
    {
        "category": "use_co2_intensity_constraint",
        "value": USE_CO2_INTENSITY_CONSTRAINT,
        "unit": "bool",
        "note": "Whether annual average CO2 intensity constraint is active.",
    },
    {
        "category": "co2_intensity_target",
        "value": CO2_INTENSITY_TCO2_PER_MWH if USE_CO2_INTENSITY_CONSTRAINT else None,
        "unit": "tCO2/MWh_load",
        "note": "Target intensity. Numerically equal to kgCO2/kWh_load.",
    },
    {
        "category": "co2_cap_from_intensity",
        "value": co2_cap_from_intensity_tco2,
        "unit": "tCO2",
        "note": "Equivalent annual CO2 cap implied by the intensity target.",
    },
    {
        "category": "co2_cap",
        "value": CO2_CAP_TCO2 if USE_CO2_CAP_CONSTRAINT else None,
        "unit": "tCO2",
        "note": "Annual CO2 cap. None if USE_CO2_CAP_CONSTRAINT=False.",
    },
    {
        "category": "use_carbon_price",
        "value": USE_CARBON_PRICE,
        "unit": "bool",
        "note": "Whether an exogenous carbon price is included in marginal costs.",
    },
    {
        "category": "carbon_price_jpy_per_tco2",
        "value": CARBON_PRICE_JPY_PER_TCO2 if USE_CARBON_PRICE else 0.0,
        "unit": "JPY/tCO2",
        "note": "Exogenous carbon price used in marginal costs.",
    },
    {
        "category": "use_co2_cap_constraint",
        "value": USE_CO2_CAP_CONSTRAINT,
        "unit": "bool",
        "note": "Whether annual CO2 cap constraint is active.",
    },
    {
        "category": "pypsa_objective",
        "value": n.objective,
        "unit": "scaled_JPY" if COST_SCALE != 1.0 else "JPY",
        "note": "Objective value reported by PyPSA. Should be close to total_system_cost if cost accounting is consistent.",
    },
])


# =========================================================
# 7. Export CSV
# =========================================================
print("Exporting CSV...")

snapshot_period_df = pd.DataFrame({
    "snapshot": n.snapshots,
    "representative_period": [SNAPSHOT_TO_PERIOD.get(ts, "") for ts in n.snapshots],
    "snapshot_weight": [SNAPSHOT_OBJECTIVE_WEIGHT for _ in n.snapshots],
})
snapshot_period_df.to_csv(f"{CSV_DIR}/snapshot_periods.csv", index=False)

gen_dispatch.to_csv(f"{CSV_DIR}/generator_dispatch.csv")
build_df.to_csv(f"{CSV_DIR}/build_summary.csv", index=False)
physical_build_summary_df.to_csv(f"{CSV_DIR}/build_summary_physical_by_carrier.csv", index=False)
if not hvdc_capacity_summary_df.empty:
    hvdc_capacity_summary_df.to_csv(f"{CSV_DIR}/hvdc_capacity_summary.csv", index=False)
generation_summary_df.to_csv(f"{CSV_DIR}/generation_summary.csv", index=False)
if not basic_mix_actual_summary_df.empty:
    basic_mix_actual_summary_df.to_csv(f"{CSV_DIR}/basic_mix_constraint_summary.csv", index=False)

if not curtailment_df.empty:
    curtailment_df.to_csv(f"{CSV_DIR}/curtailment_summary.csv", index=False)
if not nuclear_curtailment_df.empty:
    nuclear_curtailment_df.to_csv(
        f"{CSV_DIR}/nuclear_curtailment_summary.csv",
        index=False,
    )
if not emissions_df.empty:
    emissions_df.to_csv(f"{CSV_DIR}/emissions_summary.csv", index=False)

line_flow_df.to_csv(f"{CSV_DIR}/line_flow.csv")
hvdc_flow_df.to_csv(f"{CSV_DIR}/hvdc_flow.csv")
bus_price_df.to_csv(f"{CSV_DIR}/bus_marginal_price.csv")
storage_dispatch_df.to_csv(f"{CSV_DIR}/storage_dispatch.csv")
if not storage_soc_df.empty:
    storage_soc_df.to_csv(f"{CSV_DIR}/storage_state_of_charge.csv")
if not storage_soc_boundary_df.empty:
    storage_soc_boundary_df.to_csv(f"{CSV_DIR}/storage_soc_boundary_check.csv", index=False)
cost_summary_df.to_csv(f"{CSV_DIR}/cost_summary.csv", index=False)

model_settings_df = pd.DataFrame([
    {"parameter": "TIME_MODE", "value": TIME_MODE},
    {"parameter": "SCENARIO_NAME", "value": SCENARIO_NAME},
    {"parameter": "USE_CARBON_PRICE", "value": USE_CARBON_PRICE},
    {"parameter": "CARBON_PRICE_JPY_PER_TCO2", "value": CARBON_PRICE_JPY_PER_TCO2},
    {"parameter": "USE_CO2_CAP_CONSTRAINT", "value": USE_CO2_CAP_CONSTRAINT},
    {"parameter": "CO2_CAP_TCO2", "value": CO2_CAP_TCO2},
    {"parameter": "USE_CO2_INTENSITY_CONSTRAINT", "value": USE_CO2_INTENSITY_CONSTRAINT},
    {"parameter": "CO2_INTENSITY_TCO2_PER_MWH", "value": CO2_INTENSITY_TCO2_PER_MWH},
    {"parameter": "USE_BASIC_MIX_CONSTRAINT", "value": USE_BASIC_MIX_CONSTRAINT},
    {"parameter": "BASIC_MIX_DENOMINATOR", "value": BASIC_MIX_DENOMINATOR},
    {"parameter": "BASIC_MIX_FILE", "value": BASIC_MIX_FILE},
    {"parameter": "ANNUAL_HOURS", "value": ANNUAL_HOURS},
    {"parameter": "N_HOURS", "value": N_HOURS},
    {"parameter": "SNAPSHOT_OBJECTIVE_WEIGHT", "value": SNAPSHOT_OBJECTIVE_WEIGHT},
])
model_settings_df.to_csv(f"{CSV_DIR}/model_settings.csv", index=False)


# =========================================================
# 7.5 Export formatted CSVs for chart folder
# =========================================================
print("Exporting formatted CSVs (chart)...")

CHART_DIR = os.path.join(RUN_DIR, "chart")
os.makedirs(CHART_DIR, exist_ok=True)

REGION_FILE_MAP = {
    "Hokkaido": "hokkaido.csv",
    "Tohoku": "tohoku.csv",
    "Tokyo": "tokyo.csv",
    "Chubu": "chubu.csv",
    "Hokuriku": "hokuriku.csv",
    "Kansai": "kansai.csv",
    "Chugoku": "chugoku.csv",
    "Shikoku": "shikoku.csv",
    "Kyushu": "kyushu.csv",
}

SPOT_PRICE_COL_MAP = {
    "Japan": "0_Day_ahead_Japan",
    "Hokkaido": "1_Day_ahead_Hokkaido",
    "Tohoku": "2_Day_ahead_Tohoku",
    "Tokyo": "3_Day_ahead_Tokyo",
    "Chubu": "4_Day_ahead_Chubu",
    "Hokuriku": "5_Day_ahead_Hokuriku",
    "Kansai": "6_Day_ahead_Kansai",
    "Chugoku": "7_Day_ahead_Chugoku",
    "Shikoku": "8_Day_ahead_Shikoku",
    "Kyushu": "9_Day_ahead_Kyushu",
}

POWER_FLOW_ORDER = [
    ("Chugoku", "Kyushu"),
    ("Chugoku", "Shikoku"),
    ("Kansai", "Chugoku"),
    ("Kansai", "Shikoku"),
    ("Hokuriku", "Kansai"),
    ("Chubu", "Hokuriku"),
    ("Chubu", "Kansai"),
    ("Tokyo", "Chubu"),
    ("Tohoku", "Tokyo"),
    ("Hokkaido", "Tohoku"),
]


def build_datetime_columns(index):
    df = pd.DataFrame(index=index)
    df["YYYY"] = index.year
    df["MM"] = index.month
    df["DD"] = index.day
    df["h"] = index.hour
    return df


def empty_ts(index):
    return pd.Series(0.0, index=index)


def get_gen(region, carriers):
    cols = [
        g for g in n.generators.index
        if n.generators.loc[g, "bus"] == region
        and n.generators.loc[g, "carrier"] in carriers
    ]
    if not cols:
        return empty_ts(n.snapshots)
    return n.generators_t.p[cols].sum(axis=1).clip(lower=0.0)


def get_storage_dispatch(region, stype):
    cols = [
        s for s in n.storage_units.index
        if n.storage_units.loc[s, "bus"] == region
        and n.storage_units.loc[s, "carrier"] == stype
    ]
    if not cols:
        return empty_ts(n.snapshots)
    return n.storage_units_t.p[cols].sum(axis=1).clip(lower=0.0)


def get_storage_charge(region, stype):
    cols = [
        s for s in n.storage_units.index
        if n.storage_units.loc[s, "bus"] == region
        and n.storage_units.loc[s, "carrier"] == stype
    ]
    if not cols:
        return empty_ts(n.snapshots)
    return (-n.storage_units_t.p[cols].sum(axis=1)).clip(lower=0.0)


def get_import_export(region):
    net = pd.Series(0.0, index=n.snapshots)

    for line in n.lines.index:
        b0 = str(n.lines.loc[line, "bus0"])
        b1 = str(n.lines.loc[line, "bus1"])
        f = n.lines_t.p0[line]
        if region == b0:
            net -= f
        elif region == b1:
            net += f

    for link in n.links.index:
        if n.links.loc[link, "carrier"] != "HVDC":
            continue
        b0 = str(n.links.loc[link, "bus0"])
        b1 = str(n.links.loc[link, "bus1"])
        f = n.links_t.p0[link]
        if region == b0:
            net -= f
        elif region == b1:
            net += f

    return net.clip(lower=0.0), (-net).clip(lower=0.0)


def get_curtail(region, carrier):
    cols = [
        g for g in n.generators.index
        if n.generators.loc[g, "bus"] == region
        and n.generators.loc[g, "carrier"] == carrier
        and g in n.generators_t.p_max_pu
    ]
    if not cols:
        return empty_ts(n.snapshots)

    total = pd.Series(0.0, index=n.snapshots)
    for g in cols:
        pot = n.generators.loc[g, "p_nom_opt"] * n.generators_t.p_max_pu[g]
        act = n.generators_t.p[g].clip(lower=0.0)
        total += (pot - act).clip(lower=0.0)
    return total


for region in regions:
    if region not in REGION_FILE_MAP:
        continue

    df = build_datetime_columns(n.snapshots)

    df["1_Nuclear"] = get_gen(region, {"nuclear"})
    df["2_Thermal"] = get_gen(region, THERMAL_OUTPUT_CARRIERS)
    df["3_Hydro"] = get_gen(region, {"hydro", "hydro_m", "hydro_s"})
    df["4_Geothermal"] = get_gen(region, {"geothermal"})
    df["5_Biomass"] = get_gen(region, {"biomass"})
    df["6_PV"] = get_gen(region, PV_OUTPUT_CARRIERS)
    df["7_Wind"] = get_gen(region, WIND_OUTPUT_CARRIERS)

    df["8_Pumped_Hydro_Charge"] = get_storage_charge(region, "phs")
    df["9_Pumped_Hydro_Generate"] = get_storage_dispatch(region, "phs")

    imp, exp = get_import_export(region)
    df["10_Import"] = imp
    df["11_Export"] = exp

    df["12_Curtailment_PV"] = sum(
        get_curtail(region, c)
        for c in PV_OUTPUT_CARRIERS
    )
    df["13_Curtailment_Wind"] = sum(
        get_curtail(region, c)
        for c in WIND_OUTPUT_CARRIERS
    )

    for i in range(14, 19):
        df[f"{i}_Other{i-13}"] = ""

    df["19_Demand"] = load_df[region]

    ordered_cols = [
        "YYYY", "MM", "DD", "h",
        "1_Nuclear", "2_Thermal", "3_Hydro", "4_Geothermal", "5_Biomass",
        "6_PV", "7_Wind", "8_Pumped_Hydro_Charge", "9_Pumped_Hydro_Generate",
        "10_Import", "11_Export", "12_Curtailment_PV", "13_Curtailment_Wind",
        "14_Other1", "15_Other2", "16_Other3", "17_Other4", "18_Other5",
        "19_Demand",
    ]
    df = df[ordered_cols]
    df.to_csv(os.path.join(CHART_DIR, REGION_FILE_MAP[region]), index=False)

# power-flow
pf = build_datetime_columns(n.snapshots)

for i, (r0, r1) in enumerate(POWER_FLOW_ORDER, 1):
    flow = get_interconnector_flow_series(r0, r1)
    pf[f"{i}_Record_{r0}_to_{r1}"] = flow
    pf[f"{i}_Plan_{r0}_to_{r1}"] = flow

ordered_cols = ["YYYY", "MM", "DD", "h"]
for i, (r0, r1) in enumerate(POWER_FLOW_ORDER, 1):
    ordered_cols.append(f"{i}_Record_{r0}_to_{r1}")
for i, (r0, r1) in enumerate(POWER_FLOW_ORDER, 1):
    ordered_cols.append(f"{i}_Plan_{r0}_to_{r1}")

pf = pf[ordered_cols]
pf.to_csv(os.path.join(CHART_DIR, "power-flow.csv"), index=False)

# spot-price
sp = build_datetime_columns(n.snapshots)

for region in regions:
    if region in SPOT_PRICE_COL_MAP and region in bus_price_df.columns:
        sp[SPOT_PRICE_COL_MAP[region]] = bus_price_df[region]

total = load_df.sum(axis=1)
weighted = sum(bus_price_df[r] * load_df[r] for r in regions if r in bus_price_df)
sp["0_Day_ahead_Japan"] = (weighted / total).fillna(0.0)

ordered_cols = [
    "YYYY", "MM", "DD", "h",
    "0_Day_ahead_Japan",
    "1_Day_ahead_Hokkaido", "2_Day_ahead_Tohoku", "3_Day_ahead_Tokyo",
    "4_Day_ahead_Chubu", "5_Day_ahead_Hokuriku", "6_Day_ahead_Kansai",
    "7_Day_ahead_Chugoku", "8_Day_ahead_Shikoku", "9_Day_ahead_Kyushu",
]
ordered_cols = [c for c in ordered_cols if c in sp.columns]
sp = sp[ordered_cols]
sp.to_csv(os.path.join(CHART_DIR, "spot-price.csv"), index=False)

print(f"Chart CSV exported to: {CHART_DIR}")


# =========================================================
# 8. Simple plots
# =========================================================
print("Exporting plots...")

if not generation_summary_df.empty:
    ax = generation_summary_df.set_index("carrier")["generation_mwh"].plot.bar(figsize=(12, 5))
    ax.set_title("Generation Summary")
    ax.set_ylabel("MWh/year")
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/generation_summary.png", dpi=150, bbox_inches="tight")
    plt.close()

build_gen = build_df[(build_df["component"] == "Generator") & (build_df["new_build_mw"].notna())]
if not build_gen.empty:
    tmp = build_gen.groupby("carrier", as_index=False)["new_build_mw"].sum()
    ax = tmp.set_index("carrier")["new_build_mw"].plot.bar(figsize=(12, 5))
    ax.set_title("New Generator Build")
    ax.set_ylabel("MW")
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/new_generator_build.png", dpi=150, bbox_inches="tight")
    plt.close()

build_storage = build_df[(build_df["component"] == "StorageUnit") & (build_df["new_build_mw"].notna())]
if not build_storage.empty:
    tmp = build_storage.groupby("carrier", as_index=False)["new_build_mw"].sum()
    ax = tmp.set_index("carrier")["new_build_mw"].plot.bar(figsize=(8, 4))
    ax.set_title("New Storage Build")
    ax.set_ylabel("MW")
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/new_storage_build.png", dpi=150, bbox_inches="tight")
    plt.close()

print("Done.")
print(f"Run folder: {RUN_DIR}")
print(f"CSV folder: {CSV_DIR}")
print(f"Plot folder: {PLOT_DIR}")
