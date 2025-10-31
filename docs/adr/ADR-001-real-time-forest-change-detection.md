# ADR-001: Choosing a Primary Forest Data Source

**Date:** 2025-10-30  
**Status:** In Progress - Prototyping Phase  
**Authors:** Kacper Wojtaszczyk & AI Copilot

**Update History:**
- 2025-10-27: Initial draft with three candidate sources
- 2025-10-30: Added GDW experimental results and hybrid GDW + DIST-ALERT approach

---

## Context

Yuzu aims to create compelling data narratives about forest change. Before designing complex architectures or data models, we need to **find a data source that's actually pleasant to work with**.

### The Ultimate Vision

**Inspiration:** [Global Forest Review by WRI](https://gfr.wri.org/latest-analysis-deforestation-trends)

Yuzu's ultimate goal is to create an **AI-powered forest change newsletter** that:

- **Replaces human journalists with AI** for narrative generation
- **Publishes weekly** instead of quarterly/annual (higher cadence, more timely stories)
- **Emotionally engages readers** through compelling storytelling, not just data dumps
- **Makes forest loss personal and urgent** by connecting statistics to human impact

*"What if WRI's data-driven forest analysis was reimagined as AI-generated prose that painted the feeling of loss, published every week?"*

This vision constrains our data source choices—we need data that updates frequently enough to support weekly narratives and is rich enough to fuel emotionally resonant stories.

### The Problem

Initial research into forest monitoring data revealed a fragmented landscape:

- **Inconsistent methodologies**: Different datasets use different definitions of "forest," "loss," "gain," and "disturbance"
- **Spotty temporal coverage**: Some datasets update annually, others in 5-year intervals; some stopped updating years ago
- **Complex access patterns**: Mix of APIs, GeoTIFFs, Earth Engine assets, manual downloads, and proprietary portals
- **Unclear documentation**: Many sources lack clear API docs, usage examples, or version history
- **Reliability concerns**: Data quality varies; false positives, cloud cover gaps, methodology changes over time
- **Varying spatial resolution**: From 10m to 500m pixels

**Example of the mess:** Hansen/GFW provides annual tree cover loss (2000-2024), but gain data stopped at 2020 and uses 5-year intervals (2000-2005, 2005-2010, etc.). Meanwhile, there's a separate 2010 baseline tree cover layer. Combining these to calculate "current forest cover" requires assumptions that may not hold.

### What We Actually Need

Before building anything, we need **one reliable data source** that:

1. **Is accessible**: Clear API or SDK, good documentation, reasonable rate limits, no licensing nightmares
2. **Updates regularly**: At least annually, ideally more frequently
3. **Covers meaningful geography**: Tropical forests at minimum (where most deforestation occurs)
4. **Has consistent methodology**: Same definitions and processing across time; clear versioning
5. **Provides actionable metrics**: Data we can actually use to tell stories without inventing intermediate calculations
6. **Is maintainable**: Active project, responsive maintainers, clear roadmap
7. **Works with Python**: Native SDK or simple REST API

**Nice-to-have:**
- **Flexible baseline reframing**: Ability to choose different time periods as baselines depending on narrative needs or stylistic choices (e.g., "in the last week Amazon forest lost 10% of its beginning of the year cover, most of which was lost over the last month" vs "since 2015 baseline")

**Philosophy**: Start simple. Find one dataset we can rely on. Build from there. Resist the temptation to merge multiple inconsistent sources just to fill data gaps.

---

## Candidate Data Sources

### Google Dynamic World V1

**Summary:** Near real-time global 10m land use/land cover (LULC) dataset with continuous updates. Provides probability-based classification for 9 classes including "trees", generated from Sentinel-2 imagery using deep learning.

**Access:**
- **API/SDK:** Google Earth Engine Python/JavaScript API
- **Collection ID:** `GOOGLE/DYNAMICWORLD/V1`
- **Documentation:** Excellent - 3-part tutorial series, Nature paper, code examples
- **Rate limits:** Standard Earth Engine limits (free for research/education/nonprofit)
- **Authentication:** Earth Engine account required (free signup)

**Data characteristics:**
- **Temporal coverage:** 2015-06-27 to present (continuously updating)
- **Update frequency:** Every 2-5 days (matches Sentinel-2 revisit frequency)
- **Spatial resolution:** 10m
- **Geographic coverage:** Global
- **Metrics provided:** 
  - 9 probability bands (water, trees, grass, flooded_vegetation, crops, shrub_and_scrub, built, bare, snow_and_ice)
  - 1 discrete label band (0-8, highest probability class)
  - All probabilities sum to 1
  - Cloud/shadow masked using 3-step process (S2 Cloud Probability + CDI + DDT)

**Developer experience:**
- **Pleasant:** Cloud-native processing via Earth Engine, no downloads needed
- **Clean API:** Simple filtering by date and region, intuitive band selection
- **Great tutorials:** Official 3-part series with working code examples
- **Active maintenance:** Google + WRI partnership, published in Nature Scientific Data (2022)
- **Gotchas:** 
  - Requires Earth Engine platform (not raw API)
  - Single-image classifications need temporal aggregation for stability
  - Only images with <35% cloud cover are processed

**Pros:**
- **Single consistent source:** Same methodology from 2015 to present - no fragmentation
- **True NRT capability:** Updates every 2-5 days, supports weekly narratives
- **Flexible baselines:** Pick any date from 2015+ as baseline, compare to any other date
- **Probability-based:** More nuanced than binary forest/no-forest classification
- **High resolution:** 10m captures small clearings and forest edges
- **Well-validated:** 73.8% agreement with expert consensus, comparable to regional products
- **Strong trees class:** Explicitly defined as "primary and secondary forests, as well as large-scale plantations"
- **Open license:** CC-BY 4.0 (attribution only)
- **Cloud-native:** Earth Engine handles compute and storage

**Cons:**
- **Limited history:** Only back to 2015 (vs Hansen's 2000 start)
- **Platform lock-in:** Requires Earth Engine (can't easily switch)
- **Requires aggregation:** Single-image classifications are noisy; need temporal composites
- **Cloud masking imperfect:** Some misclassifications (clouds→snow, shadows→water)
- **Class confusion in arid regions:** Trees vs shrubs/crops can be ambiguous
- **No pre-computed loss product:** Must calculate change yourself
- **Methodology changes possible:** Google could update model (though V1 is versioned)
- **Google is evil:** But an evil we can work with for now

**Best for:** 
- Projects needing consistent methodology across time periods
- Near real-time monitoring and weekly/frequent updates
- Flexible temporal analysis (custom baselines and comparison periods)
- Probability-based analysis and uncertainty quantification
- Cloud-native workflows without local storage

**Worst for:** 
- Historical analysis requiring pre-2015 data
- Projects requiring complete platform independence
- Users unable to access Google Earth Engine
- Use cases needing pre-computed change products

---

### GFW Baseline (2020) + Integrated Deforestation Alerts

**Summary:** Hybrid approach using a static 2020 forest cover baseline combined with GFW's Integrated Deforestation Alerts. Alerts aggregate three detection systems (GLAD-L, GLAD-S2, RADD) into a single layer with confidence levels. Baseline and alerts use different methodologies and data structures.

**Access:**
- **Baseline datasets:**
  - Nature Trace Natural Forest 2020: `ee.ImageCollection("projects/nature-trace/assets/forest_typology/natural_forest_2020_v1_0_collection")`
  - JRC GFC2020 V2: `ee.ImageCollection("JRC/GFC2020/V2")`
  - Others available in Earth Engine catalog
- **Alerts:** GFW Data Portal + REST API (tile-based download system)
  - REST API exists but only exposes metadata and tile download links
  - Can be automated but requires significant effort (tile management, downloads, stitching)
  - Alternative: Manual click individual tiles, copy URL from popup
  - Special integer encoding: leading digit = confidence (2=low, 3=high, 4=highest), followed by days since Dec 31, 2014
- **API/SDK:** Earth Engine Python/JavaScript for baseline; GFW REST API + tile downloads for alerts
- **Documentation:** Good for baselines (Earth Engine docs); alerts documentation sparse, data portal clunky
- **Rate limits:** Standard Earth Engine limits for baseline; manual download bottleneck for alerts
- **Authentication:** Earth Engine account for baseline; GFW account for alerts portal

**Data characteristics:**
- **Temporal coverage:** 
  - Baseline: 2020 only (single snapshot)
  - Alerts: 2015-01-01 to present (but coverage varies by alert system and region)
- **Update frequency:**
  - Baseline: Static (year 2020)
  - Alerts: Daily updates (when any source system updates)
- **Spatial resolution:** 
  - Baseline: 10m
  - Alerts: 10m (GLAD-L upsampled from 30m to match Sentinel-based systems)
- **Geographic coverage:** 
  - Baseline: Global
  - Alerts: Tropics only (30°N to 30°S), with regional variations:
    - GLAD-L: Full tropics from 2018+; select countries from 2015+
    - GLAD-S2: Primary humid tropical forests South America from 2019+
    - RADD: Africa from 2019+, South America/SE Asia from 2020+
- **Metrics provided:**
  - Baseline: Binary forest/no-forest or probability of natural forest presence
  - Alerts: Single integer per pixel encoding date + confidence (low/high/highest)
  - Confidence: Low (single detection), High (detected twice), Highest (multiple systems)

**Developer experience:**
- **Baseline pleasant:** Earth Engine access, well-documented, probabilistic maps allow threshold customization
- **Alerts painful:** Tile-based architecture, REST API only provides metadata/links, requires custom tile management
- **Gotchas:**
  - **Tile-based REST API:** API exists but only returns metadata and download links; must build tile management system
  - **Complex encoding:** Each pixel is an integer where leading digit = confidence, rest = days since 2014-12-31
  - **Heterogeneous sources:** Three different alert systems with different coverage/dates
  - **Coverage gaps:** Not all regions have all alert systems; temporal coverage varies by location
  - **Retroactive changes:** Confidence levels can change as source data is updated
  - **Static baseline:** Cannot reframe baseline to different years (stuck with 2020)
  - **Multiple baseline options:** Need to choose between Nature Trace, JRC, or others
  - **Alert integration complexity:** Merging raster alerts (10m grid) with baseline requires careful spatial alignment
  - **Resampling artifacts:** GLAD-L upsampled from 30m may not align perfectly with native 10m data

**Pros:**
- **High-quality 2020 baseline:** Well-validated, 10m resolution, designed for EUDR compliance
- **Daily updates:** Alerts refresh whenever any source system updates
- **Multiple detection systems:** Three alert systems increase detection probability and confidence
- **Confidence levels:** Low/high/highest based on detection frequency and cross-system agreement
- **Established ecosystem:** GFW is widely used, trusted by conservation community
- **Longer temporal coverage:** Alerts go back to 2015 (though coverage varies)
- **Free and open:** Both baseline and alerts are publicly accessible

**Cons:**
- **Critical: Tile-based API architecture:** REST API exists but only provides metadata/links; requires building tile management system (download, stitch, spatial queries)
- **Complex data encoding:** Integer format requires decoding logic (date calculation + confidence extraction)
- **Regional coverage gaps:** Alert system coverage varies dramatically by location and time
- **No baseline flexibility:** Locked to 2020; cannot reframe to "beginning of year" or other custom dates
- **Two completely separate systems:** Baseline (Earth Engine raster) + Alerts (tile downloads) are incompatible formats
- **Inconsistent methodology:** Baseline and three alert systems all use different approaches
- **Confidence retroactivity:** Alert confidence can change later as more data arrives
- **Upsampling concerns:** 30m GLAD-L data upsampled to 10m may have alignment issues
- **Narrative limitations:** Cannot say "lost 10% since start of year" if baseline is always 2020
- **Doesn't distinguish disturbance types:** Cannot differentiate deforestation from timber harvesting or natural disturbances
- **Manual workflow:** Tile-by-tile download makes automation difficult

**Best for:**
- Projects requiring EUDR-compliant 2020 baseline
- Use cases where manual downloads are acceptable (small number of tiles)
- Stories comparing "now" vs "2020 reference"
- Organizations already integrated with GFW ecosystem
- Single-region monitoring where tile management is feasible

**Worst for:**
- **Automated pipelines:** Tile-based architecture requires significant engineering effort to automate properly
- Flexible temporal baselines (e.g., year-to-date comparisons)
- Large-scale or multi-region monitoring (too many tiles to manage)
- Weekly narratives requiring frequent data refreshes
- Use cases needing consistent methodology across time
- Projects requiring proper REST API integration

---

### Custom ML Solution (Sentinel-2 Processing)

**Summary:** Build a custom machine learning model to process Sentinel-2 imagery directly, trained specifically for forest detection and change detection. Full control over methodology, definitions, and processing, but requires significant ML expertise and computational resources.

**Access:**
- **Raw data:** Sentinel-2 imagery via Copernicus Open Access Hub or Earth Engine
- **API/SDK:** 
  - Sentinel Hub API for raw imagery
  - Earth Engine for preprocessing (if used)
  - Custom Python ML stack (TensorFlow/PyTorch, scikit-learn, etc.)
- **Documentation:** Depends on chosen ML framework and Sentinel-2 access method
- **Rate limits:** Copernicus download quotas; Earth Engine processing limits
- **Authentication:** Copernicus account; potentially Earth Engine for preprocessing

**Data characteristics:**
- **Temporal coverage:** 2015-06-23 to present (Sentinel-2A launch); complete archive available
- **Update frequency:** Every 5 days globally (2-3 days at equator with both satellites)
- **Spatial resolution:** 10m (bands 2,3,4,8); 20m (bands 5,6,7,8A,11,12); 60m (bands 1,9,10)
- **Geographic coverage:** Global
- **Metrics provided:** Whatever you train the model to produce
  - Could be: forest probability, tree cover %, change detection, disturbance classification, etc.
  - Full flexibility in output schema and granularity

**Developer experience:**
- **Complete control:** Define your own forest classes, accuracy tradeoffs, temporal aggregation
- **Heavy lifting required:** Must handle image preprocessing, cloud masking, model training, inference pipeline, validation
- **Gotchas:**
  - **Significant ML expertise required:** Need deep learning experience, remote sensing knowledge
  - **Computational resources:** Training requires GPUs; inference at scale needs serious compute
  - **Data volume:** Raw Sentinel-2 data is massive (multiple TB for global coverage)
  - **Model development time:** Months to years to achieve competitive accuracy
  - **Validation complexity:** Need labeled training data and rigorous accuracy assessment
  - **Maintenance burden:** Model drift, retraining, monitoring, debugging misclassifications
  - **Cloud masking:** Must implement or integrate cloud/shadow detection
  - **Atmospheric correction:** May need to implement or use existing tools (Sen2Cor, etc.)

**Pros:**
- **Complete independence:** No reliance on Google or other third-party providers
- **Full methodology control:** Define forest types, thresholds, and metrics to match exact needs
- **Customizable accuracy tradeoffs:** Optimize for forest detection at expense of other classes
- **Ethical alignment:** Avoid moral ambiguity of using Google products
- **Environmental control:** Choose compute infrastructure with lower carbon footprint
- **Research opportunities:** Publish papers, contribute to open source, innovate on methodology
- **No platform lock-in:** Own the entire pipeline end-to-end
- **Flexible outputs:** Design any output format or metric structure needed
- **Future-proof:** Can evolve methodology as needs change

**Cons:**
- **Massive time investment:** 6-12+ months to build competitive model from scratch
- **Requires ML expertise:** Deep learning, remote sensing, image processing skills essential
- **High computational costs:** GPU training ($$$), inference at scale requires infrastructure
- **Data storage costs:** Storing raw Sentinel-2 imagery or preprocessed features
- **Model accuracy risk:** May not match established datasets (Dynamic World: 73.8% expert agreement)
- **No peer validation:** Unlike published datasets, no external validation or comparison
- **Maintenance overhead:** Continuous monitoring, retraining, bug fixes, model updates
- **Slower time-to-value:** Cannot start building narratives until model is trained and validated
- **Reinventing the wheel:** Duplicating work already done by Google, WRI, JRC, etc.
- **Scope creep danger:** Easy to get lost in ML optimization instead of storytelling
- **No baseline comparison:** Harder to compare with established products like Hansen/GFW
- **Documentation burden:** Must document methodology for transparency and reproducibility

**Best for:**
- **Future consideration:** Not viable for MVP, but valuable long-term option
- Projects with significant ML expertise and resources
- Research-focused initiatives contributing to methodology innovation
- Organizations with ethical constraints on using commercial platforms
- Use cases requiring highly specialized forest definitions
- Long-term projects where upfront investment pays off over time
- Building differentiating IP around forest monitoring methodology

**Worst for:**
- **Hobby projects and MVPs:** Completely impractical for initial development
- Small teams without ML expertise
- Projects needing quick time-to-value
- Use cases where standard definitions are sufficient
- Organizations without GPU infrastructure or cloud compute budget
- Projects requiring immediate results or weekly narratives
- Teams that want to focus on storytelling, not ML engineering

---

## Experimental Results: Google Dynamic World Prototype

### What We Built

A prototype pipeline (`src/yuzu/pipeline/orchestration/extract_forest_metrics.py`) that:
- Aggregates Dynamic World data over configurable time windows (default: 30 days)
- Uses `mode()` for land cover label and `mean()` for tree probability
- Applies threshold-based forest classification (tested: 0.15, 0.3, 0.4, 0.5)
- Implements adaptive gap-filling: fills cloud-obscured pixels with most recent valid historical data
- Calculates forest area (hectares) for each period
- Tracks image availability and coverage completeness

### Key Findings

**✅ Gap-Filling Works:** Successfully achieved ~100% coverage across all periods by filling cloud gaps with historical aggregates.

**✅ Data Access:** Earth Engine integration is smooth, well-documented, and performant.

**❌ HIGH VOLATILITY (44.4% of average):** Forest area swings dramatically between periods:
- **Example (434,687 ha region over 23 months):**
  - Peak: 281,682 ha (April 2024)
  - Trough: 180,235 ha (November 2024)
  - Volatility: 101,447 ha (44.4% of mean)
  - Year-over-year similar month comparison still shows 10-20% variation

**Root Cause Analysis:**

1. **Seasonal Phenology Dominates Signal**
   - Dry season (Jul-Sep): Trees lose leaves, lower canopy cover → lower tree probability
   - Wet season (Dec-Mar): Full canopy → higher tree probability
   - Even with gap-filling and threshold adjustments, seasonal cycles persist

**2. Threshold Sensitivity**
   - Tested thresholds: 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8
   - Lower thresholds (0.1-0.3): More stable but include sparse vegetation
   - Mid thresholds (0.4-0.5): Balanced but still show seasonal swings
   - Higher thresholds (0.6-0.8): Capture only dense forest but amplify seasonal effects
   - **No threshold value eliminates volatility**

3. **Label-Only Approach Also Fails**
   - Using only `label` band (most probable class) without confidence threshold
   - Still shows 30-40% volatility
   - Indicates issue is in the underlying classification, not our processing

4. **Geographic Consistency**
   - Tested multiple regions (Pará/Amazonas border, São Felix do Xingu, Paraná Atlantic Forest)
   - All show similar volatility patterns
   - Rules out region-specific issues

### Critical Limitation

**Dynamic World cannot reliably separate deforestation from seasonal variation** at weekly/monthly timescales.

- Year-over-year comparisons of same season: Still 10-20% unexplained variation
- Even multi-year baselines won't eliminate within-year volatility needed for weekly narratives
- Would require complex seasonal decomposition models beyond MVP scope

**Conclusion:** Dynamic World alone is insufficient for near-real-time deforestation monitoring. We need a complementary approach.

---

### Hybrid Approach: Google Dynamic World + GLAD DIST-ALERT

**Summary:** Use Dynamic World for long-term baseline assessment and DIST-ALERT for near-real-time disturbance detection. This separates concerns: stable baselines from volatile change detection.

**Architecture:**
1. **Baseline Layer (Dynamic World):** Annual or seasonal forest cover maps aggregated over long periods (3-6 months)
2. **Change Detection (DIST-ALERT):** Daily disturbance alerts indicating vegetation loss relative to 3-year historical baseline

**DIST-ALERT Overview:**

**Data characteristics:**
- **Source:** GLAD/UMD OPERA project, NASA JPL
- **Temporal coverage:** 2022-01-01 to present
- **Update frequency:** Daily (1-day temporal resolution)
- **Spatial resolution:** 30m (Landsat + Sentinel-2 HLS fusion)
- **Geographic coverage:** Global land
- **Algorithm:** 
  - Detects vegetation loss relative to 3-year rolling baseline (31-day window)
  - Reports: vegetation cover % reduction, spectral anomaly distance
  - Baseline: All cloud-free observations from previous 3 years in 31-day window
- **Output metrics:**
  - Disturbance status (0-4: no disturbance, provisional, confirmed, historical)
  - Vegetation loss percentage
  - Anomaly magnitude
  - Confidence levels
  - Date of first detection
  - Duration of ongoing disturbance

**Access:**
- **Data format:** Cloud Optimized GeoTIFF (COG)
- **Earth Engine:** ✅ Available! (partial/recent data, sufficient for NRT monitoring)
  - **Collection path:** `projects/glad/HLSDIST/current/[LAYER_NAME]`
  - **Update frequency:** Weekly (most recent composite only)
  - **Available layers:** 14 total (9 vegetation + 5 generic disturbance)
    - VEG-DIST-STATUS, VEG-DIST-DATE, VEG-DIST-DUR, VEG-ANOM-MAX, VEG-IND, VEG-ANOM, VEG-LAST-DATE, VEG-DIST-CONF
    - GEN-DIST-STATUS, GEN-DIST-DATE, GEN-DIST-DUR, GEN-ANOM-MAX, GEN-ANOM
  - **Access pattern:** ImageCollections that are `.mosaic()`'d to single images
  - **Date encoding:** Days since 2020-12-31 (easy conversion to real dates)
  - **Example script:** https://code.earthengine.google.com/7112eeb091539055163f90c91759d1a0
  - ⚠️ **Limitation:** No historical time series in EE; full archive requires NASA downloads
  - ✅ **For weekly newsletters:** Weekly updates are PERFECT - query fresh snapshot each week, no historical archive needed
- **Download alternatives (if needed):**
  - NASA LP DAAC Earthdata (requires free account)
  - AWS S3 (potential cost/bandwidth optimization)
  - NASA Earthdata API + HTTPS download
- **Documentation:** 
  - [Algorithm Theoretical Basis Document](https://glad.umd.edu/sites/default/files/opera-dist-product-atbd-v1-final.pdf)
  - [Product Specification](https://glad.umd.edu/sites/default/files/D-108277_OPERA_DIST_HLS_Product_Specification_V1.0.pdf)
  - [Visualization App](https://glad.earthengine.app/view/dist-alert)

**How the Hybrid Works:**

```
┌─────────────────────────────────────────────────────────────┐
│ BASELINE LAYER (Dynamic World)                              │
│ - Aggregate over 3-6 months to smooth seasonality           │
│ - Update quarterly or biannually                            │
│ - Provides: "Forest exists here as of Q1 2025"              │
│ - Use for: Baseline forest extent, long-term trends         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CHANGE DETECTION (DIST-ALERT)                               │
│ - Daily disturbance alerts                                  │
│ - Detects: Vegetation loss events relative to 3yr baseline  │
│ - Provides: "Disturbance detected on Oct 23, 2025"          │
│ - Use for: Weekly newsletter, NRT monitoring                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ NARRATIVE LAYER                                              │
│ - Overlay DIST alerts on GDW baseline                       │
│ - "250 ha of forest (baseline: Q1 2025) disturbed this week"│
│ - Track alert→confirmation→historical status progression    │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ **Separation of concerns:** Baseline (stable, low-frequency) vs Change (volatile, high-frequency)
- ✅ **Daily updates:** DIST-ALERT enables true NRT monitoring
- ✅ **Reduces false positives:** DIST's 3-year baseline accounts for seasonal variation
- ✅ **Confidence levels:** Provisional → Confirmed → Historical status tracking
- ✅ **Complementary resolutions:** 10m (GDW) for baseline, 30m (DIST) for change is acceptable trade-off
- ✅ **Both in Earth Engine:** DIST recent data available in EE, simplifies integration
- ✅ **Multiple download options:** NASA LP DAAC, AWS S3 for cost/bandwidth optimization
- ✅ **Both global:** Worldwide coverage, no geographic gaps
- ✅ **Well-validated:** DIST published in Nature Communications (2025), UMD/GLAD track record
- ✅ **NASA-backed:** OPERA project ensures longevity and maintenance
- ✅ **Baseline flexibility:** GDW is working assumption; alternative baseline datasets possible if better match found

**Cons:**
- ❌ **Two separate systems:** Must coordinate baseline updates with alert processing
- ❌ **DIST in EE may be incomplete:** Recent data available, but full archive may require downloads
- ❌ **Resolution mismatch:** 10m (GDW) vs 30m (DIST) requires spatial alignment
- ❌ **Increased complexity:** Must manage baseline updates + alert processing logic
- ❌ **Baseline refresh strategy:** Need to define when/how to update baseline (annually? quarterly?)
- ❌ **Baseline dataset TBD:** GDW is placeholder; may switch to better-matched dataset during prototyping
- ❌ **Alert interpretation:** Must understand DIST status codes and confidence levels
- ❌ **Data freshness lag:** DIST alerts may take 1-3 days to appear in distribution system

**Best for:**
- Weekly forest change newsletters (this project!)
- Near-real-time disturbance monitoring with stable baselines
- Projects needing both "what's there" and "what changed" narratives
- Use cases where daily updates matter more than 10m resolution
- Organizations comfortable with hybrid cloud/download workflows

**Worst for:**
- Single-system simplicity (introduces architectural complexity)
- Real-time (< 1 day) response requirements
- Pixel-perfect 10m change detection (30m DIST may miss small clearings)
- Projects requiring pure Earth Engine workflows
- MVP implementations (more complex than single-source approach)

**Implementation Notes:**

1. **Baseline Strategy:**
   - Generate baseline once per year (or quarter, TBD during prototyping)
   - **Baseline dataset:** Currently assuming GDW, but open to alternatives with:
     - 30m resolution (matches DIST)
     - More static/stable methodology
     - Annual or better update frequency
   - Store as static raster for the period
   - Use for all weekly newsletters until next baseline update

2. **DIST Integration:**
   - **Primary:** Use Earth Engine access for recent alerts (simplest integration)
     ```python
     # Access DIST layers in Earth Engine
     folder = "projects/glad/HLSDIST/current"
     veg_status = ee.ImageCollection(f"{folder}/VEG-DIST-STATUS").mosaic()
     veg_dist_date = ee.ImageCollection(f"{folder}/VEG-DIST-DATE").mosaic()
     veg_anom_max = ee.ImageCollection(f"{folder}/VEG-ANOM-MAX").mosaic()
     veg_conf = ee.ImageCollection(f"{folder}/VEG-DIST-CONF").mosaic()
     
     # Filter for recent, high-confidence disturbances
     days_since_2020 = (datetime.now() - datetime(2020, 12, 31)).days
     recent_threshold = days_since_2020 - 7  # Last 7 days
     recent_dist = veg_dist_date.gte(recent_threshold).And(veg_status.gte(1))
     ```
   - **Backup:** Set up download workflow from NASA LP DAAC or AWS S3 if EE coverage insufficient
   - Filter alerts within our regions of interest
   - Cross-reference with current baseline
   - Track alert status progression (provisional → confirmed → historical)

3. **Narrative Template:**
   ```
   "This week, DIST-ALERT detected 450 hectares of vegetation disturbance
   in the São Felix do Xingu region. Of this, 320 hectares occurred in 
   areas classified as forest in our 2025 baseline, representing a 2.1% 
   loss of the region's forest cover. The largest single event (85 ha) 
   was first detected on October 23 and confirmed on October 25."
   ```

**Status:** Proposed for prototyping phase. Requires feasibility testing of:
- DIST Earth Engine access: coverage, update frequency, historical depth
- Baseline dataset selection (GDW vs alternatives)
- Spatial overlay of 30m DIST alerts on baseline
- Alert status tracking and narrative generation logic
- Performance and cost optimization (EE vs download workflows)

---

## Decision

**[PLACEHOLDER: Selected data source and rationale]**

We will use **[Source Name]** as our primary forest data source because:

1. [Key reason 1]
2. [Key reason 2]
3. [Key reason 3]

### What We're Building (Initially)

**[PLACEHOLDER: Minimal viable data pipeline description]**

- Extract [what data] from [source]
- Store [which metrics] in [format/database]
- Enable queries like: [example question 1], [example question 2]

### What We're Explicitly NOT Doing

**[PLACEHOLDER: Anti-scope to avoid over-engineering]**

- NOT merging multiple inconsistent data sources
- NOT inventing derived metrics without clear methodology
- NOT building real-time monitoring (unless source naturally supports it)
- NOT attempting to build ML models for change detection
- NOT [other tempting features to avoid]

---

## Consequences

### Positive

**[PLACEHOLDER: Expected benefits]**

- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

### Negative

**[PLACEHOLDER: Accepted limitations and tradeoffs]**

- [Limitation 1]
  - **Mitigation:** [How we'll handle it]
- [Limitation 2]
  - **Mitigation:** [How we'll handle it]

### Technical Debt

**[PLACEHOLDER: Things we're deferring or will need to revisit]**

- [Debt item 1]
- [Debt item 2]

---

## Monitoring Triggers

Review this decision if:

- **API reliability drops below [X]%** or documentation degrades (measured how?)
- **Update frequency changes** significantly (delays or stops)
- **Methodology changes** in ways that break historical comparisons
- **Better alternative emerges** with clearer API and more actionable data
- **Geographic coverage** no longer meets Yuzu's needs
- **Cost or rate limits** become prohibitive
- **Community/maintainer support** disappears
- **I will be in the mood** for ML algorithms and custom change detection

---

## Implementation Notes

**[PLACEHOLDER: First steps and technical setup]**

### Initial Setup
```bash
# [Authentication/API key setup]
# [SDK installation]
# [Test query examples]
```

### Data Schema (Minimal)
```sql
-- [Placeholder for initial database schema]
-- Focus on storing what the API gives us, not inventing fields
```

### First Query
```python
# [Placeholder for simplest possible data extraction]
# Goal: Prove we can reliably pull data for one region
```

---

## References

**[PLACEHOLDER: Documentation and research links]**

- [Data source official docs]
- [API reference]
- [Relevant papers or methodology docs]
- [Example notebooks or community projects]

---


## Follow-up Tasks

**[PLACEHOLDER: Immediate next steps after decision]**

1. [ ] Set up API access / authentication
2. [ ] Design minimal database schema for chosen data
3. [ ] Implement single-region extraction as proof of concept
4. [ ] Validate data quality and update frequency claims
5. [ ] Document any surprises or gotchas discovered during integration
