CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS slope_analyses (
    id           SERIAL PRIMARY KEY,
    created_at   TIMESTAMP DEFAULT NOW(),
    name         TEXT,
    transect     GEOMETRY(LINESTRING, 4326),
    fos          FLOAT,
    srf_steps    JSONB,
    dat_filename TEXT
);

CREATE INDEX IF NOT EXISTS idx_slope_analyses_transect ON slope_analyses USING GIST (transect);
