# ADR-001: Real-Time Forest Change Detection Strategy

**Date:** 2025-10-15  
**Status:** Accepted  
**Authors:** Kacper Wojtaszczyk & AI Copilot

---

## Context

Yuzu's goal is to narrate deforestation and forest-health changes as close to real time as possible — ideally with a **1- to 4-week delay**.

The initial data model assumed **Hansen/UMD Global Forest Watch** (GFW) annual loss data would serve as the primary forest change indicator. However, investigation revealed critical limitations:

- **Loss data latency**: 12-18 months (e.g., 2024 data available mid-2025)
- **Gain data**: Stopped at 2020, never updated
- **Temporal resolution**: Annual snapshots only
- **Impact**: Yuzu would report events 1+ year after they occurred, contradicting the "living chronicle" vision

**Core requirement:** Yuzu should generate narratives with **1-4 week latency** to feel current and relevant, balancing timeliness with data credibility.

---

## Geographic Scope

**This decision establishes Yuzu's focus on tropical and subtropical forests (30°N to 30°S).**

This limitation is inherent to the chosen real-time alert systems (GLAD and RADD), which were designed specifically for tropical deforestation monitoring.

### ✅ Covered Regions
- **Amazon Basin**: Brazil, Peru, Colombia, Venezuela, Ecuador, Bolivia
- **Congo Basin**: Democratic Republic of Congo, Republic of Congo, Cameroon, Central African Republic, Gabon
- **Southeast Asia**: Indonesia (Sumatra, Kalimantan, Papua), Malaysia (Sabah, Sarawak), Papua New Guinea, Philippines
- **Central America**: Costa Rica, Panama, Guatemala, Honduras, Nicaragua
- **West Africa**: Ghana, Ivory Coast, Liberia, Sierra Leone
- **South Asia**: Parts of India, Bangladesh, Myanmar, Thailand, Vietnam
- **Northern Australia**: Queensland tropical forests
- **Madagascar**: Eastern rainforests

### ❌ Not Covered (MVP)
- **Boreal forests**: Canada, Russia, Scandinavia, Alaska
- **Temperate forests**: US Pacific Northwest, Europe (Germany, Poland, Romania), China, Japan, New Zealand, southern Chile/Argentina
- **High-latitude regions**: Any forests beyond 30°N or 30°S latitude

**Rationale:** ~60% of global deforestation occurs in tropical regions, making this the highest-impact focus area for environmental storytelling. Tropical forests also represent the most biodiverse and carbon-dense ecosystems under threat.

**Future expansion:** See monitoring triggers below for conditions under which global coverage becomes feasible.

---

## Decision

We will adopt a **hybrid two-layer architecture**:

### Layer 1: Historical Baseline (Annual)
- **Source**: Hansen/UMD GFW tree cover loss (2000-2024, v1.12)
- **Access method**: Google Earth Engine Python API
  - Asset ID: `UMD/hansen/global_forest_change_2024_v1_12`
  - Requires GEE account and project ID
- **Temporal resolution**: Annual only (no sub-annual data available)
  - Hansen dataset reports year of loss, not month/week
  - Attempting finer granularity would be inventing data
- **Purpose**: 
  - Establish annual historical loss rates per region
  - Validate and calibrate real-time alerts (when multi-year alert data accumulates)
  - Provide multi-decade context for narratives
- **Update frequency**: Manual extraction when new GFW data releases (typically September)
- **Configuration**:
  - Tree cover threshold: 30% canopy cover (configurable per region)
  - Year range: Parameterized (extract 1-2 years at a time for testing, full 2000-2024 for production)
  - Coordinate system: WGS84 (EPSG:4326)

### Layer 2: Near-Real-Time Disturbances (Weekly)
- **Primary source**: GLAD alerts (University of Maryland via Google Earth Engine)
  - 30m resolution, weekly updates
  - 7-14 day latency
  - Tropical/subtropical coverage (30°N to 30°S)
  - Confidence levels: use only "high confidence" detections
  
- **Secondary source**: RADD alerts (Wageningen University via GEE)
  - 10m resolution, Sentinel-1 radar (cloud-penetrating)
  - 6-12 day latency
  - Fills gaps in cloudy regions
  
- **Fire detection**: NASA FIRMS (MODIS + VIIRS)
  - Near real-time thermal anomaly detection
  - <24 hour latency
  - Complements disturbance alerts with fire context

- **Vegetation health**: Sentinel-2 NDVI
  - 5-day revisit, 2-5 day processing latency
  - Tracks forest vigor and recovery trends
  
- **Purpose**:
  - Detect disturbances within 1-2 weeks of occurrence
  - Feed current-year data into chronicles
  - Enable anomaly detection (e.g., "this week 40% above October average")

### Narrative Approach

**Terminology distinction**:
- **"Disturbance"**: Real-time alerts indicating canopy change (may include logging, fire damage, storms)
- **"Loss"**: Validated permanent tree cover reduction (annual GFW data only)

**Example chronicle entry**:
> "In the week ending October 8, disturbance alerts covered 2.4 km² — the highest weekly rate since July's fire season. Year-to-date, alerts total 38 km², tracking 15% above the 2020-2023 baseline."

---

## Alternatives Considered

### Alternative 1: Continue with GFW annual data only
**Pros:**
- Stable, well-validated academic source
- Simple architecture
- Easy to integrate (static GeoTIFFs, CSVs)
- High validation quality
- Great for historical analysis
- No cloud-cover issues

**Cons:**
- 12-18 month lag makes narratives feel historical, not living
- Multi-month to multi-year delay
- No week-to-week variability
- Misses time-sensitive events (fires, illegal logging rushes)
- Defeats Yuzu's core value proposition

**Best for:** Academic retrospectives, research, baselines  
**Worst for:** Near-real-time storytelling, live storytelling

**Rejected because:** Latency incompatible with project goals; fails Yuzu's near-real-time objective.

---

### Alternative 2: Real-time alerts only (no GFW baseline)
**Pros:**
- Maximum freshness (1-2 week latency)
- Simplest data pipeline
- Weekly to daily updates (alerts and fires)
- Combines optical + radar + thermal signals
- Global coverage with open access

**Cons:**
- No historical context ("is this normal?")
- Alert confidence varies; needs calibration
- Can't validate if disturbance = permanent loss
- Higher noise / false positives (especially GLAD)
- Larger data-volume management overhead
- Requires cloud masking, smoothing, and calibration

**Best for:** Emergency monitoring systems, responsive narrative-driven systems  
**Worst for:** Contextual storytelling, static dashboards or precise year-end statistics

**Rejected because:** Context is essential for meaningful narratives; selected as part of hybrid approach instead.

---

### Alternative 3: Sentinel-2 time-series change detection (custom model)
**Pros:**
- Full control over detection algorithm
- 5-day revisit, ~1 week latency
- Global coverage

**Cons:**
- Requires training custom ML model (high complexity)
- Cloud masking challenges in tropics
- Validation against ground truth needed
- Significant engineering investment

**Best for:** Research organizations with ML teams  
**Worst for:** Early-stage hobby project

**Rejected because:** Complexity outweighs benefits when GLAD/RADD exist.

---

### Alternative 4: Commercial or high-res sources (Planet NICFI, Global Land Analysis PRO)
**Pros:**
- Monthly 5m–10m imagery
- Excellent spatial detail for storytelling visuals
- Free NICFI access for tropics (non-commercial use)
- Superior resolution for visual narratives

**Cons:**
- Licensing constraints for open redistribution
- API quotas and heavier preprocessing
- Complex to automate globally
- Monthly latency (not weekly)
- Non-commercial restrictions may limit Yuzu's future use cases

**Best for:** Regional deep dives, high-quality visualizations for specific areas  
**Worst for:** Continuous global automation, fully open-source projects

**Deferred:** May integrate as optional high-res visual layer in Phase 3; not suitable as primary detection source.

---

## Consequences

### Positive
- **Achieves 1-2 week latency** for chronicles
- **Maintains accuracy** via dual validation (alerts + annual baseline)
- **Leverages existing tools** (Google Earth Engine, proven algorithms)
- **Scalable**: GLAD/RADD cover all tropical forests globally
- **Honest**: Narratives distinguish "alerts" from "confirmed loss"
- Weekly or even daily story cadence becomes feasible
- Diverse data types (optical, radar, thermal) enable richer narrative context
- Modular ingestion design encourages later expansion

### Negative
- **Geographic limitation**: GLAD alerts cover only tropics (30°N-30°S)
  - Excludes boreal forests (Canada, Russia, Scandinavia)
  - Excludes temperate forests (US Pacific Northwest, Europe, China)
  - **Mitigation**: Document coverage limits; consider RADD expansion or wait for GLAD-L (global version in development)
  
- **Complexity increase**: Two-layer data model requires:
  - GEE integration (Python API)
  - Alert aggregation pipeline
  - Baseline comparison logic
  - **Mitigation**: Treat as phased implementation (baseline first, then alerts)

- **Cloud cover gaps**: Optical alerts (GLAD) fail in persistent cloud cover
  - **Mitigation**: RADD radar alerts fill gaps; narrative acknowledges data limitations

- **Alert vs. loss ambiguity**: Not all disturbances = permanent deforestation
  - Selective logging may show regrowth
  - Storm damage may recover
  - **Mitigation**: Annual GFW validation; narratives use precise language

- **False positives from GLAD** require post-processing and confidence scoring
- **Data volume and rate limits** may need caching or batching strategies
- **Maintaining consistency** across data versions could be challenging

### Technical Debt
- Need Google Earth Engine account (free for research/education)
- Alert data stored separately from annual loss (schema complexity)
- Validation pipeline to compare alerts vs. GFW when annual data releases

### Monitoring Triggers

Review this decision if:
- **API reliability drops below 90%** (consider alternative providers)
- **GLAD-L (global GLAD) becomes operational** (removes tropical-only limitation)
- **GFW reduces latency significantly** (unlikely given Landsat processing constraints)
- **Yuzu expands to boreal/temperate forests** (requires alternative alert systems)
- **Custom change-detection models become tractable** (if ML expertise joins project)
- **Newer open datasets become available** with better latency/accuracy
- **Storage or compute costs** exceed expected limits

---

## Implementation Notes

### Data Schema
```sql
-- Region definitions with geometry
CREATE TABLE forest_regions (
    region_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_name VARCHAR(255) NOT NULL,
    region_type VARCHAR(50),  -- 'country', 'state', 'protected_area', 'custom'
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    
    -- Config overrides (NULL = use defaults)
    tree_cover_threshold INT,  -- Override global 30% default if needed
    baseline_year INT DEFAULT 2000,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Historical baseline (Hansen GFW)
CREATE TABLE forest_annual_loss (
    region_id UUID REFERENCES forest_regions(region_id),
    year INT NOT NULL,
    
    -- Metrics
    loss_km2 NUMERIC(10, 3) NOT NULL,
    baseline_cover_km2 NUMERIC(10, 3) NOT NULL,  -- Year 2000 baseline
    
    -- Provenance tracking
    tree_cover_threshold INT NOT NULL,
    dataset_version VARCHAR(20) NOT NULL,
    extracted_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (region_id, year)
);

-- Real-time alerts (Phase 2 - future)
CREATE TABLE forest_disturbance_alerts (
    region_id UUID REFERENCES forest_regions(region_id),
    week_ending DATE NOT NULL,
    glad_alerts_km2 NUMERIC(10, 3),
    radd_alerts_km2 NUMERIC(10, 3),
    combined_disturbance_km2 NUMERIC(10, 3),
    confidence_level VARCHAR(10), -- 'high', 'medium', 'low'
    PRIMARY KEY (region_id, week_ending)
);

-- Indexes for common queries
CREATE INDEX idx_annual_loss_year ON forest_annual_loss(year);
CREATE INDEX idx_regions_name ON forest_regions(region_name);
CREATE INDEX idx_regions_geom ON forest_regions USING GIST(geometry);

-- Derived metrics for narratives
CREATE VIEW current_year_activity AS
SELECT 
    region_id,
    SUM(combined_disturbance_km2) AS ytd_disturbance_km2,
    AVG(combined_disturbance_km2) AS weekly_avg_km2
FROM forest_disturbance_alerts
WHERE EXTRACT(YEAR FROM week_ending) = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY region_id;
```

### Google Earth Engine Integration
```python
import ee

# Authenticate once
ee.Authenticate()
ee.Initialize()

# Query GLAD alerts for region
glad = ee.ImageCollection('projects/glad/alert/UpdResult')
region_geom = ee.Geometry.Rectangle([minLon, minLat, maxLon, maxLat])

# Filter to past week, high confidence only
alerts = glad.filterDate('2025-10-01', '2025-10-08') \
             .filterBounds(region_geom) \
             .select('conf19') \
             .map(lambda img: img.eq(3))  # 3 = high confidence

# Aggregate pixel count → km²
stats = alerts.sum().multiply(ee.Image.pixelArea()) \
              .divide(1e6) \
              .reduceRegion(reducer=ee.Reducer.sum(),
                            geometry=region_geom,
                            scale=30)
```

### Phased Rollout
1. **Phase 1** (weeks 1-2): Implement GFW baseline ingestion + storage
2. **Phase 2** (weeks 3-4): Add GLAD alert pipeline
3. **Phase 3** (week 5): Integrate comparison logic ("X% above baseline")
4. **Phase 4** (week 6): Add RADD for cloud-cover gaps
5. **Validation** (ongoing): When new GFW annual data releases, compare to cumulative alerts

### Data Confidence Scoring

Implement tiered confidence levels:
- **High confidence**: GLAD high + RADD agreement + FIRMS fire detected
- **Medium confidence**: Single source alert without corroboration
- **Low confidence**: Edge pixels, cloud-adjacent, or isolated detections

Apply smoothing via rolling 2-week averages to reduce noise in narrative generation.

---

## References

- **GLAD Alerts**: Hansen et al., "High-Resolution Global Maps of 21st-Century Forest Cover Change" (Science, 2013) + operational updates
- **RADD System**: Reiche et al., "Forest disturbance alerts for the Congo Basin using Sentinel-1" (Env. Res. Letters, 2021)
- **Google Earth Engine**: [earthengine.google.com](https://earthengine.google.com)
- **GFW Data Portal**: [data.globalforestwatch.org](https://data.globalforestwatch.org)
- **Global Forest Watch API (Alerts)**: [https://data-api.globalforestwatch.org](https://data-api.globalforestwatch.org)
- **RADD Alerts Dashboard**: [https://www.globalforestwatch.org/map/?map=tree-cover-loss-radd](https://www.globalforestwatch.org/map/?map=tree-cover-loss-radd)
- **NASA FIRMS API**: [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)
- **Sentinel Hub & Copernicus Data Space**: [https://dataspace.copernicus.eu](https://dataspace.copernicus.eu)
- **Planet NICFI**: [https://developers.planet.com/docs/nicfi/](https://developers.planet.com/docs/nicfi/)

---

## Follow-up Tasks

1. Set up Google Earth Engine Python API
2. Design forest regions table (geographic boundaries)
3. Implement GFW baseline ingestion (see implementation notes above)
4. Prototype GLAD alert aggregation pipeline
5. Define data confidence scoring and smoothing logic
6. Build initial test region pipeline (e.g., Amazon Pará) for validation
