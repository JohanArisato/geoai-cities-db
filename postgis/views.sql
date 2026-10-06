-- Spatial views for PostGIS. Run after load.sh has copied the GeoPackage layers.
-- Note: ogr2ogr lowercases column names (NetUnits -> netunits).
-- Each view recomputes a cross-project question with a live spatial join.

-- ogr2ogr copies the GeoPackage's SQLite views as plain tables; replace them with real views.
DROP TABLE IF EXISTS v_curbcall_area_summary, v_shade_priorities, v_project_data;

-- Use the real housing layers when present, otherwise the synthetic sample.
DO $$
BEGIN
  IF to_regclass('public.sd_housing_sites') IS NULL
     AND to_regclass('public.sd_housing_sites_synthetic') IS NOT NULL THEN
    EXECUTE 'CREATE VIEW sd_housing_sites AS SELECT * FROM sd_housing_sites_synthetic';
  END IF;
END $$;

-- CurbCall: resident reports per area, assigned by the report's location (examples excluded).
CREATE OR REPLACE VIEW v_reports_by_area AS
SELECT n.area_name,
       COUNT(r.fid) FILTER (WHERE NOT r.is_example) AS resident_reports,
       COUNT(r.fid) FILTER (WHERE r.is_example)     AS example_reports
FROM sd_neighborhoods n
LEFT JOIN curbcall_reports r ON ST_Within(r.geom, n.geom)
GROUP BY n.area_name;

-- Housing: claimed capacity per neighborhood, using each site's interior point.
CREATE OR REPLACE VIEW v_housing_capacity_by_neighborhood AS
SELECT n.name AS neighborhood,
       n.area_name,
       COUNT(s.fid)                     AS sites,
       COALESCE(SUM(s.netunits), 0)   AS claimed_units
FROM sd_neighborhoods n
LEFT JOIN sd_housing_sites s ON ST_Within(ST_PointOnSurface(s.geom), n.geom)
GROUP BY n.name, n.area_name;

-- Cross-project: where residents report problems near sites the city counts on for housing.
-- (Distance in meters via geography.)
CREATE OR REPLACE VIEW v_reports_near_housing_sites AS
SELECT r.report_id, r.title, r.type, s.site_id,
       ROUND(ST_Distance(r.geom::geography, s.geom::geography)) AS meters
FROM curbcall_reports r
JOIN sd_housing_sites s ON ST_DWithin(r.geom::geography, s.geom::geography, 400);

-- New York: planting priorities with a ready-made map geometry.
CREATE OR REPLACE VIEW v_shade_priorities AS
SELECT name, borough, surface_temp_f, tree_canopy_pct, poverty_pct, heat_ed_rate,
       rank_canopy_gap, rank_equity_weighted, top10_share,
       (top10_share >= 0.9) AS robust_priority, geom
FROM nyc_uhf42_shade
ORDER BY rank_equity_weighted;

-- Which project uses which data, and whether it is synthetic.
CREATE OR REPLACE VIEW v_project_data AS
SELECT p.slug AS project, p.title, pl.layer, pl.role, c.rows, c.synthetic, c.source
FROM projects p
JOIN project_layers pl ON pl.project = p.slug
JOIN layer_catalog c ON c.layer = pl.layer
ORDER BY p.slug, pl.layer;
