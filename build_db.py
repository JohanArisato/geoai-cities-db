"""Build geoai_cities.gpkg: one spatial database shared by every project.

    python build_db.py                    # San Diego housing from the City's live services
    python build_db.py --housing sample   # offline: synthetic housing sample (flagged)
    python build_db.py --housing none     # skip housing layers

The output is a GeoPackage (an SQLite file with geometry) that opens in
QGIS, ArcGIS Pro, DuckDB, GeoPandas or plain sqlite3. `postgis/` loads the
same layers into PostgreSQL + PostGIS.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "data" / "vendor"
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "geoai_cities.gpkg"
CRS = "EPSG:4326"

SD_NEIGHBORHOODS_URL = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
                        "main/public/data/san-diego.geojson")
HOUSING_SERVICE = ("https://webmaps.sandiego.gov/arcgis/rest/services/Planning/"
                   "PLN_Housing_ServiceLayers/MapServer")
HOUSING_SAMPLE = ROOT.parent / "housing-site-realization" / "data" / "sample"

PROJECTS = [
    ("housing-site-realization", "Will It Get Built? Predicting Which Housing Element Sites Are Realized",
     "https://github.com/JohanArisato/housing-site-realization", "In progress"),
    ("who-gets-the-shade", "Who Gets the Shade? Ranking New York Neighborhoods for Tree Planting",
     "https://github.com/JohanArisato/who-gets-the-shade", "Working paper"),
    ("curbcall", "CurbCall: Resident-Ranked Infrastructure Repairs for San Diego",
     "https://github.com/JohanArisato/curbcall", "Prototype"),
    ("geoai-for-cities", "GeoAI for Cities: Research Series and Website",
     "https://github.com/JohanArisato/geoai-for-cities", "Ongoing"),
]

CATALOG: list[dict] = []
PROJECT_LAYERS: list[tuple[str, str, str]] = []


def register(layer, title, source, url, license_, year, description, rows, synthetic=False,
             projects=()):
    CATALOG.append(dict(layer=layer, title=title, source=source, url=url, license=license_,
                        year=year, description=description, rows=rows, synthetic=int(synthetic),
                        built=date.today().isoformat()))
    for slug, role in projects:
        PROJECT_LAYERS.append((slug, layer, role))


def write(gdf: gpd.GeoDataFrame | pd.DataFrame, layer: str):
    if isinstance(gdf, gpd.GeoDataFrame):
        gdf.to_crs(CRS).to_file(OUT, layer=layer, driver="GPKG", engine="pyogrio")
    else:
        with sqlite3.connect(OUT) as con:
            gdf.to_sql(layer, con, if_exists="replace", index=False)


def _polygons(geom):
    """Keep only polygonal parts (make_valid can return collections) as a MultiPolygon."""
    from shapely.geometry import MultiPolygon
    parts = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type in ("Polygon", "MultiPolygon")]
    flat = [p for g in parts for p in getattr(g, "geoms", [g])]
    return MultiPolygon(flat)


def fetch(url: str, path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {url}")
        urllib.request.urlretrieve(url, path)
    return path


def arcgis_layer(layer_url: str, page: int = 2000) -> gpd.GeoDataFrame:
    """Page through a public ArcGIS REST layer and return it as a GeoDataFrame."""
    feats, offset = [], 0
    while True:
        q = (f"{layer_url}/query?where=1%3D1&outFields=*&outSR=4326&f=geojson"
             f"&orderByFields=OBJECTID&resultOffset={offset}&resultRecordCount={page}")
        with urllib.request.urlopen(q, timeout=120) as r:
            batch = json.load(r).get("features", [])
        feats += batch
        if len(batch) < page:
            break
        offset += page
    return gpd.GeoDataFrame.from_features(feats, crs=CRS)


# ---------------------------------------------------------------------------
def build_san_diego():
    raw = gpd.read_file(fetch(SD_NEIGHBORHOODS_URL, CACHE / "san-diego.geojson"))
    meta = json.loads((VENDOR / "sd_neighborhood_areas.json").read_text())
    hoods = raw[["name", "geometry"]].copy()
    hoods["geometry"] = hoods.geometry.make_valid().apply(_polygons)  # fix a few self-intersections
    hoods["area_name"] = hoods.name.map(meta["neighborhood_area"])
    assert hoods["area_name"].notna().all(), "every neighborhood needs an area"
    hoods.insert(0, "neighborhood_id", range(1, len(hoods) + 1))
    hoods["area_order"] = hoods["area_name"].map({a: i for i, a in enumerate(meta["areas"], 1)})
    hoods["acres"] = (hoods.to_crs(2230).area / 43560).round(1)
    write(hoods, "sd_neighborhoods")
    register("sd_neighborhoods", "San Diego neighborhoods (124)", "Code for America, Click That 'Hood",
             SD_NEIGHBORHOODS_URL, "Open (see source)", "2013",
             "City of San Diego neighborhood polygons, each assigned to one of seven CurbCall areas.",
             len(hoods), projects=[("curbcall", "geography"), ("housing-site-realization", "context")])

    areas = hoods.dissolve("area_name", as_index=False, aggfunc={"area_order": "first", "acres": "sum",
                                                            "neighborhood_id": "count"})
    areas = areas.rename(columns={"neighborhood_id": "n_neighborhoods"}).sort_values("area_order")
    write(areas, "sd_areas")
    register("sd_areas", "San Diego areas (7)", "Derived from sd_neighborhoods", "", "Derived", "2026",
             "Seven areas used for fair, per-area rankings: North, Coast, Mesas & Valley, "
             "Downtown & Uptown, Mid-City, Southeast, South Bay.", len(areas),
             projects=[("curbcall", "ranking units")])

    rep = gpd.read_file(VENDOR / "curbcall_example_reports.geojson")
    rep = gpd.sjoin(rep, hoods[["neighborhood_id", "area_name", "geometry"]], how="left",
                    predicate="within").drop(columns="index_right")
    write(rep, "curbcall_reports")
    register("curbcall_reports", "CurbCall reports", "CurbCall prototype",
             "https://github.com/JohanArisato/curbcall", "CC BY 4.0", "2026",
             "Resident infrastructure reports. The current rows are labeled EXAMPLES written to "
             "demonstrate the app (is_example = 1), not resident data.", len(rep),
             projects=[("curbcall", "reports")])
    return hoods, rep


def build_housing(mode: str, hoods: gpd.GeoDataFrame):
    if mode == "none":
        return None
    if mode == "real":
        print("  fetching Housing Element sites and permits from the City of San Diego ...")
        sites = arcgis_layer(f"{HOUSING_SERVICE}/1")
        permits = arcgis_layer(f"{HOUSING_SERVICE}/0")
        suffix, synthetic, src = "", False, "City of San Diego, Planning Department"
    else:
        sites = gpd.read_file(HOUSING_SAMPLE / "sites.geojson")
        permits = gpd.read_file(HOUSING_SAMPLE / "permits.geojson")
        sites = sites.drop(columns=[c for c in sites if c.startswith("_")])
        suffix, synthetic, src = "_synthetic", True, "Synthetic sample (housing-site-realization)"

    keep = [c for c in ["APN_8", "SITE_ID", "CPNAME", "ACRES", "ExtgUnits", "PotenUnits", "NetUnits",
                        "HIGHDEN", "Extg_Landuse", "TPAHIIP", "CTCAC", "Ov_CZ", "Ov_CHLOZ"] if c in sites]
    sites = sites[keep + ["geometry"]].copy()
    if "APN_8" in sites:
        sites["APN_8"] = sites["APN_8"].astype(str)
    cent = sites.geometry.to_crs(2230).centroid.to_crs(CRS)
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=cent, crs=CRS), hoods[["name", "area_name", "geometry"]],
                  how="left", predicate="within")
    j = j[~j.index.duplicated()]
    sites["neighborhood"], sites["area_name"] = j["name"], j["area_name"]
    write(sites, f"sd_housing_sites{suffix}")
    register(f"sd_housing_sites{suffix}", "Housing Element adequate sites (2021-2029)", src,
             f"{HOUSING_SERVICE}/1", "Public record", "2021",
             "Parcels the City inventoried as able to hold new housing, with zoned capacity."
             + (" SYNTHETIC: generated to mirror the real schema; not real parcels." if synthetic else ""),
             len(sites), synthetic, projects=[("housing-site-realization", "unit of analysis")])

    pcols = [c for c in ["APPROVAL_ID", "APPROVAL_TYPE", "APPROVAL_ISSUE_DATE", "JOB_APN", "TOTAL_DU",
                         "TOTAL_ADU", "TOTAL_JADU", "GIS_COMM_PLAN_NAME"] if c in permits]
    permits = permits[pcols + ["geometry"]].copy()
    if "APPROVAL_ISSUE_DATE" in permits and pd.api.types.is_numeric_dtype(permits.APPROVAL_ISSUE_DATE):
        v = permits.APPROVAL_ISSUE_DATE.astype("float64")
        permits["APPROVAL_ISSUE_DATE"] = pd.to_datetime(v, unit="ms" if v.abs().max() > 1e11 else "s").dt.date.astype(str)
    write(permits, f"sd_housing_permits{suffix}")
    register(f"sd_housing_permits{suffix}", "Housing approvals (DSD)", src, f"{HOUSING_SERVICE}/0",
             "Public record", "2018-", "Development approvals with dwelling-unit counts."
             + (" SYNTHETIC." if synthetic else ""), len(permits), synthetic,
             projects=[("housing-site-realization", "outcome")])
    return sites


def build_nyc():
    shade = gpd.read_file(VENDOR / "nyc_uhf42_shade.geojson")
    write(shade, "nyc_uhf42_shade")
    register("nyc_uhf42_shade", "NYC UHF42 heat, canopy and poverty", "NYC DOHMH Environment & Health "
             "Data Portal; analysis by who-gets-the-shade", "https://github.com/nycehs/All_EHDP_Data",
             "Public", "2009-2017", "Surface temperature, tree canopy, vegetation, poverty and heat-stress "
             "ER visits for 42 NYC neighborhoods, with planting ranks and robustness shares.",
             len(shade), projects=[("who-gets-the-shade", "analysis table"), ("geoai-for-cities", "maps")])


def build_summaries(hoods, reports, sites):
    """Pre-computed spatial joins so plain SQL (no spatial extension) can answer cross-project questions."""
    s = pd.DataFrame(hoods[["neighborhood_id", "name", "area_name", "acres"]])
    r = reports[~reports.is_example.astype(bool)] if "is_example" in reports else reports
    s["curbcall_reports"] = s.neighborhood_id.map(r.groupby("neighborhood_id").size()).fillna(0).astype(int)
    s["curbcall_example_reports"] = s.neighborhood_id.map(
        reports.groupby("neighborhood_id").size()).fillna(0).astype(int)
    if sites is not None:
        g = sites.groupby("neighborhood")
        s["housing_sites"] = s.name.map(g.size()).fillna(0).astype(int)
        s["housing_claimed_units"] = s.name.map(g.NetUnits.sum()).fillna(0).astype(int)
    write(pd.DataFrame(s), "sd_neighborhood_summary")
    register("sd_neighborhood_summary", "San Diego neighborhood summary", "Derived", "", "Derived",
             "2026", "One row per neighborhood joining CurbCall reports and Housing Element sites.",
             len(s), synthetic=bool(sites is not None and "_synthetic" in CATALOG[-2]["layer"]),
             projects=[("curbcall", "research view"), ("housing-site-realization", "research view")])


def write_catalog():
    with sqlite3.connect(OUT) as con:
        pd.DataFrame(CATALOG).to_sql("layer_catalog", con, if_exists="replace", index=False)
        pd.DataFrame(PROJECTS, columns=["slug", "title", "repo", "status"]).to_sql(
            "projects", con, if_exists="replace", index=False)
        pd.DataFrame(PROJECT_LAYERS, columns=["project", "layer", "role"]).to_sql(
            "project_layers", con, if_exists="replace", index=False)
        con.executescript((ROOT / "geoai_db" / "views.sql").read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--housing", choices=["real", "sample", "none"], default="real")
    args = ap.parse_args()
    OUT.unlink(missing_ok=True)
    print("San Diego ...")
    hoods, reports = build_san_diego()
    print(f"Housing ({args.housing}) ...")
    sites = build_housing(args.housing, hoods)
    print("New York ...")
    build_nyc()
    build_summaries(hoods, reports, sites)
    write_catalog()
    print(f"\nBuilt {OUT.name} ({OUT.stat().st_size / 1e6:.1f} MB):")
    print(pd.DataFrame(CATALOG)[["layer", "rows", "synthetic"]].to_string(index=False))


if __name__ == "__main__":
    main()
