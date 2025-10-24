-- Initialize PostGIS extension and create basic schema
-- This runs automatically when the PostgreSQL container first starts

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create schema for forest data
CREATE SCHEMA IF NOT EXISTS forest;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA forest TO yuzu;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA forest TO yuzu;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA forest TO yuzu;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA forest GRANT ALL ON TABLES TO yuzu;
ALTER DEFAULT PRIVILEGES IN SCHEMA forest GRANT ALL ON SEQUENCES TO yuzu;

-- Create forest regions table
CREATE TABLE IF NOT EXISTS forest.forest_regions (
    region_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_name VARCHAR(255) NOT NULL,
    region_type VARCHAR(50),  -- 'country', 'state', 'protected_area', 'custom'
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,

    -- Config overrides (NULL = use defaults)
    tree_cover_threshold INT CHECK (tree_cover_threshold >= 0 AND tree_cover_threshold <= 100),
    baseline_year INT DEFAULT 2000,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create forest annual loss table (Hansen GFW baseline)
CREATE TABLE IF NOT EXISTS forest.forest_annual_loss (
    region_id UUID REFERENCES forest.forest_regions(region_id) ON DELETE CASCADE,
    year INT NOT NULL CHECK (year >= 2000 AND year <= 2100),

    -- Metrics
    loss_km2 NUMERIC(10, 3) NOT NULL CHECK (loss_km2 >= 0),
    baseline_cover_km2 NUMERIC(10, 3) NOT NULL CHECK (baseline_cover_km2 >= 0),

    -- Provenance tracking
    tree_cover_threshold INT NOT NULL CHECK (tree_cover_threshold >= 0 AND tree_cover_threshold <= 100),
    dataset_version VARCHAR(20) NOT NULL,
    extracted_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (region_id, year)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_annual_loss_year ON forest.forest_annual_loss(year);
CREATE INDEX IF NOT EXISTS idx_regions_name ON forest.forest_regions(region_name);
CREATE INDEX IF NOT EXISTS idx_regions_geom ON forest.forest_regions USING GIST(geometry);

-- Add comments for documentation
COMMENT ON TABLE forest.forest_regions IS 'Geographic regions for forest monitoring (protected areas, countries, custom boundaries)';
COMMENT ON TABLE forest.forest_annual_loss IS 'Annual forest loss data from Hansen/UMD GFW baseline (2000-2024)';
COMMENT ON COLUMN forest.forest_annual_loss.loss_km2 IS 'Forest loss area in square kilometers for the year';
COMMENT ON COLUMN forest.forest_annual_loss.baseline_cover_km2 IS 'Year 2000 baseline forest cover in square kilometers';
COMMENT ON COLUMN forest.forest_annual_loss.dataset_version IS 'Hansen dataset version (e.g., v1.12)';

-- Confirm setup
SELECT PostGIS_Version();

