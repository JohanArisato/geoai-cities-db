"""Questions that span projects, answered from the shared database.

    python examples/cross_project_queries.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import geopandas as gpd  # noqa: E402

from geoai_db import catalog, read, sql  # noqa: E402

print("What's in the database\n", catalog().to_string(index=False), "\n")

print("1. Which projects use which data?")
print(sql("SELECT project, layer, role, synthetic FROM v_project_data").to_string(index=False), "\n")

print("2. NYC: robust tree-planting priorities")
print(sql("SELECT name, borough, poverty_pct, heat_ed_rate, top10_share "
          "FROM v_shade_priorities WHERE robust_priority = 1").to_string(index=False), "\n")

print("3. San Diego: housing capacity the inventory claims, by CurbCall area")
print(sql("SELECT area_name, SUM(housing_sites) AS sites, SUM(housing_claimed_units) AS claimed_units "
          "FROM sd_neighborhood_summary GROUP BY area_name ORDER BY claimed_units DESC").to_string(index=False))
synthetic = sql("SELECT MAX(synthetic) s FROM layer_catalog WHERE layer LIKE 'sd_housing%'").s.iloc[0]
if synthetic:
    print("   (housing layers are the SYNTHETIC sample; run `python build_db.py` for real data)\n")

print("4. Spatial join in Python: CurbCall reports within 400 m of a housing site")
layer = [l for l in catalog().layer if l.startswith("sd_housing_sites")][0]
sites = read(layer).to_crs(2230)
reports = read("curbcall_reports").to_crs(2230)
near = gpd.sjoin_nearest(reports, sites[["SITE_ID", "geometry"]], max_distance=1312, distance_col="feet")
print(near[["title", "SITE_ID", "feet"]].assign(meters=lambda d: (d.feet * .3048).round())
      .drop(columns="feet").head(8).to_string(index=False))
