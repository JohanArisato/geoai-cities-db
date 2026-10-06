#!/usr/bin/env bash
# Load geoai_cities.gpkg into PostgreSQL + PostGIS (Supabase, Neon, local Postgres, ...).
#   export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
#   ./postgis/load.sh
# Requires GDAL's ogr2ogr/ogrinfo and psql. Safe to re-run.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GPKG="${1:-$HERE/../geoai_cities.gpkg}"
: "${DATABASE_URL:?Set DATABASE_URL to your Postgres connection string}"

# Drop our views first so tables can be replaced (CASCADE also drops views other repos built on them).
psql "$DATABASE_URL" -q -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['v_reports_by_area','v_housing_capacity_by_neighborhood',
      'v_reports_near_housing_sites','v_shade_priorities','v_project_data','v_curbcall_area_summary',
      'sd_housing_sites']
  LOOP
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = v AND relkind = 'v') THEN
      EXECUTE format('DROP VIEW %I CASCADE', v);
    END IF;
  END LOOP;
END $$;
SQL

# Tables only: skip the GeoPackage's SQLite views (v_*), which are recreated as PostGIS views.
LAYERS=$(ogrinfo -q "$GPKG" | sed -E 's/^[0-9]+: ([^ ]+).*/\1/' | grep -v '^v_')
# shellcheck disable=SC2086
ogr2ogr -f PostgreSQL "PG:$DATABASE_URL" "$GPKG" $LAYERS \
  -overwrite -lco GEOMETRY_NAME=geom -lco FID=fid -lco SPATIAL_INDEX=GIST \
  -nlt PROMOTE_TO_MULTI --config PG_USE_COPY YES
psql "$DATABASE_URL" -q -v ON_ERROR_STOP=1 -f "$HERE/views.sql"
echo "Loaded: $(echo $LAYERS | wc -w) layers. Try: psql \"\$DATABASE_URL\" -c 'SELECT * FROM v_reports_by_area;'"
