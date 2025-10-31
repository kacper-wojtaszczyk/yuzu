# Yuzu Methodology

**Last Updated:** October 30, 2025  
**Status:** Living document—will evolve as we learn and expand

---

## Purpose

This document explains how Yuzu works with forest data and generates narratives. Unlike traditional forest monitoring reports that combine dozens of datasets with complex methodologies, Yuzu starts simple and builds incrementally. We document what we actually do, not what we might do someday.

---

## Data Sources

### Selection Criteria

Yuzu prioritizes data sources that are:
- **Accessible:** Clear API/SDK, good documentation, reasonable rate limits
- **Maintained:** Active development, responsive maintainers, clear roadmap
- **Consistent:** Same methodology across time periods
- **Transparent:** Documented algorithms, validation, known limitations

Specific datasets are documented in Architecture Decision Records (ADRs) in `docs/adr/`. Currently under evaluation: see [ADR-001](adr/ADR-001-real-time-forest-change-detection.md).

---

## Data Processing

### Area Calculations

All area calculations account for Earth's curvature:
- Geodesic area is calculated per pixel (area varies with latitude)
- Areas are summed within regions of interest (countries, custom polygons)
- Results reported in hectares (ha)

### Classification and Thresholds

Forest classification depends on the source dataset methodology:
- Where applicable, we document threshold values used (e.g., probability cutoffs, canopy density)
- We prefer using the most probable class or highest confidence classification
- Threshold selection is documented and justified in ADRs

### Regional Aggregation

We aggregate data by:
- **Custom polygons:** User-defined regions stored in PostGIS database
- **Administrative boundaries:** Using standard geographic identifiers
- **Ecological boundaries:** When relevant and well-defined

No attempt is made to reclassify land use, distinguish natural from planted forests, or infer causality of loss. We report what the satellite data shows.

---

## Database Storage

### Schema Design Philosophy

Our PostgreSQL + PostGIS database stores:
- **Source metrics:** Data as provided by satellite/remote sensing sources
- **Calculated derived metrics:** Aggregations, rates, percentages computed from source data
- **Spatial geometries:** Regions of interest as PostGIS polygons
- **Metadata:** Data extraction timestamps, source dataset versions, processing parameters

**What we don't invent:**
- No metrics that require unsupported assumptions about the data
- No land-use classifications beyond what source data provides
- No interpolation or gap-filling (unless explicitly documented)
- No predictive modeling

**Principle:** If a metric can't be directly computed or clearly derived from source data with documented methodology, we don't store it.

---

## Narrative Generation with LLMs

### The AI Component

Yuzu uses Large Language Models (LLMs) to transform forest data into prose narratives. This is where we diverge from traditional monitoring reports.

**Current approach:**
1. Extract quantitative metrics from database
2. Format as structured data payload
3. Send to LLM with narrative generation prompt
4. Parse and validate LLM output

**LLM Interface Design:**
- **Provider-agnostic:** Abstracted interface allows switching between OpenAI, Anthropic, local models, etc.
- **Prompt structure:** Separates data context, tone instructions, and output format requirements
- **Temperature:** Currently using low temperature (0.2-0.3) for consistent, grounded outputs

### Fact Grounding Strategy

This is critical: **every quantitative claim in generated narratives must map to a known metric.**

**Validation process:**
1. LLM generates narrative with inline data references (e.g., `{metric: tree_cover_loss_2023}`)
2. Post-processing validates all references against source data
3. Flagged if LLM invents numbers or makes unsupported claims
4. Rejected narratives go back for regeneration with stricter constraints

**Example acceptable claim:**
> "In 2023, this region lost 12,450 hectares of tree cover, a 15% increase from the previous year."

Both numbers (12,450 ha, 15% increase) must be present in the source data.

**Example unacceptable claim:**
> "This forest loss likely displaced hundreds of wildlife species."

"Hundreds of wildlife species" is not in our data—it's LLM speculation.

### Tone and Style Control

We configure LLM tone through prompt engineering:
- **Emotionally engaging** but factually grounded
- **Personal and urgent** without sensationalism
- **Concrete imagery** tied to measurable change
- **Avoid jargon** while maintaining accuracy

The goal is WRI-style data storytelling but with AI speed and weekly cadence.

### Reproducibility

- Same input data + same prompt + same model + same seed → should produce same narrative
- We log: model version, temperature, prompt template version, timestamp
- Narratives are versioned and traceable to source data snapshots

---

## Limitations and Honest Caveats

### What Yuzu Can Tell You

- Forest disturbance and change events within monitored regions
- Temporal trends based on available data timespan
- Comparative analysis between regions
- Changes relative to documented baselines

### What Yuzu Cannot Tell You

- **Why loss occurred:** Fire, logging, agriculture, natural disturbance? Causality requires additional data and analysis
- **Complete ground truth:** Satellite data has inherent limitations (cloud cover, resolution, classification errors)
- **Forest quality or biodiversity:** Remote sensing captures structure, not ecological richness
- **Socioeconomic impacts:** We don't model human displacement, economic costs, carbon markets, etc.
- **Future projections:** We report historical and near-real-time data, not predictions

### The LLM Uncertainty Factor

**LLMs introduce a new kind of limitation:**
- **Plausible-sounding errors:** Models can generate statistically fluent text that contains subtle inaccuracies
- **Contextual drift:** Longer narratives may lose grounding in data
- **Cultural/political bias:** Models trained on internet text carry embedded biases
- **Hallucination risk:** Despite validation, some invented details may slip through

**Our mitigation strategy:**
- Strict fact-grounding validation (every number must be traceable)
- Short narrative formats reduce drift
- Human review of all generated content (for the time being)
- Transparent labeling: readers know narratives are AI-generated

**We are experimenting with AI journalism.** Mistakes will happen. When they do, we'll document them and improve the process.

---

## Quality Assurance

### Data Pipeline Validation

- **Automated tests:** Every data extraction includes sanity checks appropriate to the data source
- **Cross-validation:** Where possible, compare results against established monitoring systems
- **Version tracking:** Log source dataset versions and processing parameters for each extraction
- **Coverage monitoring:** Track data availability and quality metrics per region

### Narrative Validation

- **Human review** of all narratives before publication
- **Fact grounding verification:** All quantitative claims traced to source data
- **User feedback loop:** Readers can flag suspect claims
- **Quality assessment:** Prose clarity, readability, emotional impact (subjective but documented)

### What We Don't Validate (Yet)

- Cultural appropriateness of framing (requires domain expertise)
- Deep fact-checking beyond numeric claims (e.g., historical context)
- Long-term reproducibility across dataset methodology changes

---

## Evolution and Transparency

### This Document Will Change

As Yuzu grows, so will this methodology. Updates might include:
- Additional data sources (when we actually integrate them, not before)
- New analytical techniques (if we implement them)
- Improved LLM validation (as we learn what fails)
- Expanded geographic coverage (when technically feasible)

**Every significant change triggers:**
1. Update to this document with date stamp
2. Rationale explaining why the change was made
3. Assessment of impact on historical comparisons

### What We Won't Do

- Retroactively change historical narratives to match new methodologies
- Merge incompatible datasets without clear documentation of assumptions
- Add complexity for its own sake

---

## References

Dataset-specific citations and technical references are maintained in:
- **Architecture Decision Records:** `docs/adr/` for data source decisions
- **Code documentation:** Inline citations in processing modules
- **Generated narratives:** Source attribution for each published story

This approach ensures references stay current as data sources evolve.
- Global Forest Watch. [https://www.globalforestwatch.org/](https://www.globalforestwatch.org/)
- Google Earth Engine Data Catalog: Hansen Global Forest Change. [https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11)

---

## Contact

Questions about methodology? Found an error? Create a github issue.

This is a hobby project exploring AI-powered data storytelling. We welcome critique, skepticism, and suggestions.
