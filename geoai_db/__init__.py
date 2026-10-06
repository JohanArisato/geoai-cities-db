"""Tiny helper for the shared GeoAI Cities database.

    from geoai_db import read, sql, catalog
    hoods = read("sd_neighborhoods")                       # GeoDataFrame
    sql("SELECT * FROM v_shade_priorities LIMIT 5")        # DataFrame
    catalog()                                              # what's inside, sources, synthetic flags

Set GEOAI_DB to point at a copy of geoai_cities.gpkg somewhere else.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import geopandas as gpd
import pandas as pd

DEFAULT = Path(__file__).resolve().parents[1] / "geoai_cities.gpkg"


def path() -> Path:
    p = Path(os.environ.get("GEOAI_DB", DEFAULT))
    if not p.exists():
        raise FileNotFoundError(f"{p} not found. Run `python build_db.py` in geoai-cities-db first.")
    return p


def read(layer: str, **kwargs) -> gpd.GeoDataFrame:
    """Read one spatial layer (or attribute table) as a (Geo)DataFrame."""
    return gpd.read_file(path(), layer=layer, **kwargs)


def sql(query: str, params=()) -> pd.DataFrame:
    """Run read-only SQL against the GeoPackage (attribute tables and views)."""
    with sqlite3.connect(f"file:{path()}?mode=ro", uri=True) as con:
        return pd.read_sql_query(query, con, params=params)


def catalog() -> pd.DataFrame:
    return sql("SELECT layer, title, rows, synthetic, source, year FROM layer_catalog")


def require_real(layer: str) -> None:
    """Raise if a layer is synthetic, so analyses meant for publication can't use it by accident."""
    flag = sql("SELECT synthetic FROM layer_catalog WHERE layer = ?", (layer,))
    if flag.empty:
        raise KeyError(layer)
    if int(flag.synthetic.iloc[0]):
        raise ValueError(f"{layer} is synthetic sample data, not suitable for findings.")
