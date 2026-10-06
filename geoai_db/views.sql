-- Attribute views that work in any SQLite client (no spatial extension needed).
-- The PostGIS versions in postgis/views.sql compute the same answers with live spatial joins.

DROP VIEW IF EXISTS v_curbcall_area_summary;
CREATE VIEW v_curbcall_area_summary AS
SELECT a.area_name,
       a.n_neighborhoods,
       COALESCE(SUM(s.curbcall_reports), 0)          AS resident_reports,
       COALESCE(SUM(s.curbcall_example_reports), 0)  AS example_reports
FROM sd_areas a
LEFT JOIN sd_neighborhood_summary s ON s.area_name = a.area_name
GROUP BY a.area_name, a.n_neighborhoods, a.area_order
ORDER BY a.area_order;

DROP VIEW IF EXISTS v_shade_priorities;
CREATE VIEW v_shade_priorities AS
SELECT name, borough, surface_temp_f, tree_canopy_pct, poverty_pct, heat_ed_rate,
       rank_canopy_gap, rank_equity_weighted, top10_share,
       CASE WHEN top10_share >= 0.9 THEN 1 ELSE 0 END AS robust_priority
FROM nyc_uhf42_shade
ORDER BY rank_equity_weighted;

DROP VIEW IF EXISTS v_project_data;
CREATE VIEW v_project_data AS
SELECT p.slug AS project, p.title, pl.layer, pl.role, c.rows, c.synthetic, c.source
FROM projects p
JOIN project_layers pl ON pl.project = p.slug
JOIN layer_catalog c ON c.layer = pl.layer
ORDER BY p.slug, pl.layer;
