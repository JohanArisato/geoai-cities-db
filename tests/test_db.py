import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest  # noqa: E402

from geoai_db import catalog, read, require_real, sql  # noqa: E402


def test_layers_and_counts():
    c = catalog().set_index("layer")
    assert c.loc["sd_neighborhoods", "rows"] == 124
    assert c.loc["sd_areas", "rows"] == 7
    assert c.loc["nyc_uhf42_shade", "rows"] == 42


def test_geometry_and_crs():
    hoods = read("sd_neighborhoods")
    assert hoods.crs.to_epsg() == 4326
    assert hoods.geometry.is_valid.all()
    assert (hoods.geom_type == "MultiPolygon").all()
    assert hoods.area_name.notna().all()


def test_every_report_lands_in_a_neighborhood():
    r = read("curbcall_reports")
    assert r.neighborhood_id.notna().all()


def test_views_answer():
    assert len(sql("SELECT * FROM v_curbcall_area_summary")) == 7
    assert sql("SELECT SUM(robust_priority) n FROM v_shade_priorities").n.iloc[0] == 6


def test_synthetic_guard():
    synthetic = catalog().query("synthetic == 1").layer.tolist()
    for layer in synthetic:
        with pytest.raises(ValueError):
            require_real(layer)
    require_real("nyc_uhf42_shade")
