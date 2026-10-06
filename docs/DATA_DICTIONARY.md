# Data dictionary

Generated from `geoai_cities.gpkg` by `docs/make_dictionary.py`.

## `sd_neighborhoods`

San Diego neighborhoods (124). 124 rows, MultiPolygon geometry.
Source: Code for America, Click That 'Hood (2013).

| Column | Type | Example |
|---|---|---|
| `neighborhood_id` | int64 | 1 |
| `name` | str | Qualcomm |
| `area_name` | str | Mesas & Valley |
| `area_order` | int64 | 3 |
| `acres` | float64 | 169.5 |

## `sd_areas`

San Diego areas (7). 7 rows, MultiPolygon geometry.
Source: Derived from sd_neighborhoods (2026).

| Column | Type | Example |
|---|---|---|
| `area_name` | str | North |
| `area_order` | int64 | 1 |
| `acres` | float64 | 100112.5 |
| `n_neighborhoods` | int64 | 19 |

## `curbcall_reports`

CurbCall reports. 17 rows, Point geometry.
Source: CurbCall prototype (2026).

| Column | Type | Example |
|---|---|---|
| `report_id` | str | ex01 |
| `type` | str | Crosswalk |
| `title` | str | Faded crosswalk on a busy shopping corne |
| `where_text` | str | Mira Mesa Blvd at Camino Ruiz |
| `details` | str | Example report: drivers turning right do |
| `neighborhood` | str | Mira Mesa |
| `checklist` | str | Paint faded/Poor lighting at night |
| `is_example` | bool | True |
| `created_at` | int64 | 1759500000000 |
| `neighborhood_id` | int64 | 50 |
| `area_name` | str | North |

## `sd_housing_sites_synthetic` **(synthetic)**

Housing Element adequate sites (2021-2029). 6000 rows, Polygon geometry.
Source: Synthetic sample (housing-site-realization) (2021).

| Column | Type | Example |
|---|---|---|
| `APN_8` | str | 81076411 |
| `SITE_ID` | str | S000000 |
| `CPNAME` | str | Carmel Valley |
| `ACRES` | float64 | 2.237 |
| `ExtgUnits` | int32 | 1 |
| `PotenUnits` | int32 | 84 |
| `NetUnits` | int32 | 83 |
| `HIGHDEN` | int32 | 44 |
| `Extg_Landuse` | str | Single Family |
| `TPAHIIP` | int32 | 0 |
| `CTCAC` | str | Highest Resource |
| `Ov_CZ` | str | Yes |
| `Ov_CHLOZ` | str | Yes |
| `neighborhood` | str | Carmel Valley |
| `area_name` | str | North |

## `sd_housing_permits_synthetic` **(synthetic)**

Housing approvals (DSD). 2383 rows, Point geometry.
Source: Synthetic sample (housing-site-realization) (2018-).

| Column | Type | Example |
|---|---|---|
| `APPROVAL_ID` | str | PMT-0000000 |
| `APPROVAL_TYPE` | str | Building Permit - New Construction |
| `APPROVAL_ISSUE_DATE` | str | 2024-09-25 |
| `JOB_APN` | str | 4812281400 |
| `TOTAL_DU` | int32 | 5 |
| `TOTAL_ADU` | int32 | 0 |
| `TOTAL_JADU` | int32 | 0 |
| `GIS_COMM_PLAN_NAME` | str | Rancho Bernardo |

## `nyc_uhf42_shade`

NYC UHF42 heat, canopy and poverty. 42 rows, MultiPolygon geometry.
Source: NYC DOHMH Environment & Health Data Portal; analysis by who-gets-the-shade (2009-2017).

| Column | Type | Example |
|---|---|---|
| `uhf` | int32 | 101 |
| `name` | str | Kingsbridge - Riverdale |
| `borough` | str | Bronx |
| `surface_temp_f` | float64 | 90.4 |
| `tree_canopy_pct` | float64 | 46.9313 |
| `vegetation_pct` | float64 | 61.9 |
| `poverty_pct` | float64 | 15.19 |
| `heat_ed_rate` | float64 | 5.47 |
| `top10_share` | float64 | 0.0 |
| `rank_canopy_gap` | int32 | 42 |
| `rank_equity_weighted` | int32 | 42 |

## `sd_neighborhood_summary` **(synthetic)**

San Diego neighborhood summary. 124 rows.
Source: Derived (2026).

| Column | Type | Example |
|---|---|---|
| `neighborhood_id` | int64 | 1 |
| `name` | str | Qualcomm |
| `area_name` | str | Mesas & Valley |
| `acres` | float64 | 169.5 |
| `curbcall_reports` | int64 | 0 |
| `curbcall_example_reports` | int64 | 0 |
| `housing_sites` | int64 | 1 |
| `housing_claimed_units` | int64 | 11 |
