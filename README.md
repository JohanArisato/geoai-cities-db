# GeoAI Cities DB

> 🌐 [Interactive database explorer](https://johanarisato.github.io/geoai-for-cities/explore/database.html) · [GeoAI for Cities](https://johanarisato.github.io/geoai-for-cities/) · [Portfolio](https://johanarisato.github.io/Johan.github.io/)

**One spatial database behind every project in my GeoAI for Cities research.**

Each of my projects asks a version of the same question, *who gets what in cities?*, but each started with its own data files. This repository puts them in one place: a single GeoPackage (`geoai_cities.gpkg`) with San Diego and New York layers, a catalog that records where every layer came from and whether it is real or synthetic, and views that answer questions spanning projects.

It opens anywhere: QGIS, ArcGIS Pro, GeoPandas, DuckDB or plain `sqlite3`. The same layers load into PostgreSQL + PostGIS with one script.

## What's inside

| Layer | Rows | What it is | Used by |
|---|---|---|---|
| `sd_neighborhoods` | 124 | San Diego neighborhoods, each in one of 7 areas | CurbCall, Housing |
| `sd_areas` | 7 | North, Coast, Mesas & Valley, Downtown & Uptown, Mid-City, Southeast, South Bay | CurbCall |
| `curbcall_reports` | 17 | Resident infrastructure reports (current rows are labeled examples) | CurbCall |
| `sd_housing_sites` | ~thousands | 2021–2029 Housing Element adequate sites | Housing |
| `sd_housing_permits` | ~thousands | Development approvals with unit counts | Housing |
| `nyc_uhf42_shade` | 42 | Heat, canopy, poverty and heat-illness for NYC neighborhoods, with planting ranks | Who Gets the Shade |
| `sd_neighborhood_summary` | 124 | Reports and housing capacity joined per neighborhood | CurbCall, Housing |
| `layer_catalog`, `projects`, `project_layers` | | Source, license, year, row count and **synthetic flag** for every layer; which project uses what | All |

Views: `v_curbcall_area_summary`, `v_shade_priorities`, `v_project_data`. Column-level details are in [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md).

> **Real vs. synthetic.** The committed database was built offline, so its housing layers are the synthetic sample from `housing-site-realization` (named `*_synthetic` and flagged in `layer_catalog`). Run `python build_db.py` with internet access to replace them with the City of San Diego's live data. `geoai_db.require_real(layer)` raises an error if an analysis tries to use synthetic data.

## Quick start

```bash
pip install -r requirements.txt
python build_db.py                    # rebuild with live San Diego housing data
python build_db.py --housing sample   # offline build (synthetic housing, flagged)
pytest -q
python examples/cross_project_queries.py
```

```python
from geoai_db import read, sql, catalog

hoods = read("sd_neighborhoods")                                  # GeoDataFrame
sql("SELECT * FROM v_shade_priorities WHERE robust_priority = 1")  # DataFrame
catalog()                                                         # sources and flags
```

```sql
-- plain sqlite3, no extensions
SELECT area_name, SUM(housing_claimed_units) FROM sd_neighborhood_summary GROUP BY area_name;
```

## PostGIS

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"   # Supabase or Neon free tiers work
./postgis/load.sh
psql "$DATABASE_URL" -c "SELECT * FROM v_housing_capacity_by_neighborhood ORDER BY claimed_units DESC LIMIT 10;"
```

`postgis/views.sql` recomputes the summaries with live spatial joins (`ST_Within`, `ST_DWithin`), including `v_reports_near_housing_sites`: resident-reported problems within 400 m of sites the city counts on for new housing.

## Questions this makes possible

- Do neighborhoods the Housing Element counts on for new homes also have the most unresolved sidewalk, lighting and flooding problems? (CurbCall × Housing)
- Are the areas with the most claimed capacity the ones residents rank last for repairs?
- Do the equity patterns in New York tree planting appear in San Diego once canopy and heat layers are added?

## Sources

| Layer | Source |
|---|---|
| San Diego neighborhoods | [Code for America, Click That 'Hood](https://github.com/codeforamerica/click_that_hood) |
| Housing sites and approvals | [City of San Diego Planning, Housing service layers](https://webmaps.sandiego.gov/arcgis/rest/services/Planning/PLN_Housing_ServiceLayers/MapServer) |
| NYC heat, canopy, poverty, heat illness | [NYC DOHMH Environment & Health Data Portal](https://github.com/nycehs/All_EHDP_Data); [UHF42 boundaries](https://github.com/nycehs/NYC_geography) |
| CurbCall reports | [CurbCall](https://github.com/JohanArisato/curbcall) |

Code: MIT. Data: under each source's terms.

## Part of

[GeoAI for Cities](https://github.com/JohanArisato/geoai-for-cities) · [Who Gets the Shade?](https://github.com/JohanArisato/who-gets-the-shade) · [CurbCall](https://github.com/JohanArisato/curbcall) · [Will It Get Built?](https://github.com/JohanArisato/housing-site-realization)
