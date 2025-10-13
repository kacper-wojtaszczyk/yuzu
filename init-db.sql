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

-- Confirm setup
SELECT PostGIS_Version();

