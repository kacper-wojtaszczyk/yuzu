-- Insert test region: Monte Pascoal National Park, Brazil
-- A small protected area (~225 km²) in Bahia with documented deforestation
-- Good for testing: tropical forest, manageable size, known forest loss patterns

INSERT INTO forest.forest_regions (
    region_id,
    region_name,
    region_type,
    geometry,
    tree_cover_threshold,
    baseline_year
) VALUES (
    '550e8400-e29b-41d4-a716-446655440001',  -- Fixed UUID for easy reference
    'Monte Pascoal National Park',
    'protected_area',
    ST_GeomFromGeoJSON('{
        "type": "Polygon",
        "coordinates": [[
            [-39.25, -16.95],
            [-39.25, -16.75],
            [-39.05, -16.75],
            [-39.05, -16.95],
            [-39.25, -16.95]
        ]]
    }'),
    30,  -- 30% tree cover threshold
    2000
);

-- Verify insertion
SELECT
    region_id,
    region_name,
    region_type,
    tree_cover_threshold,
    ST_Area(geography(geometry)) / 1000000 as area_km2,
    ST_AsGeoJSON(geometry) as geometry_json
FROM forest.forest_regions
WHERE region_id = '550e8400-e29b-41d4-a716-446655440001';

