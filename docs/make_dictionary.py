"""Regenerate docs/DATA_DICTIONARY.md from the built database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyogrio  # noqa: E402

from geoai_db import catalog, path, read  # noqa: E402

lines = ["# Data dictionary", "", "Generated from `geoai_cities.gpkg` by `docs/make_dictionary.py`.", ""]
cat = catalog().set_index("layer")
for layer, geom in pyogrio.list_layers(path()):
    if layer not in cat.index:
        continue
    c = cat.loc[layer]
    df = read(layer)
    flag = " **(synthetic)**" if c.synthetic else ""
    lines += [f"## `{layer}`{flag}", "", f"{c.title}. {c['rows']} rows" + (f", {geom} geometry." if geom else "."),
              f"Source: {c.source} ({c.year}).", "", "| Column | Type | Example |", "|---|---|---|"]
    for col in [x for x in df.columns if x != "geometry"]:
        ex = df[col].dropna().iloc[0] if df[col].notna().any() else ""
        ex = str(ex)[:40].replace("|", "/")
        lines.append(f"| `{col}` | {df[col].dtype} | {ex} |")
    lines.append("")
Path(__file__).with_name("DATA_DICTIONARY.md").write_text("\n".join(lines))
print("wrote DATA_DICTIONARY.md")
