# Yuzu Methodology

**Last Updated:** October 27, 2025  
**Status:** Living document—will evolve as we learn and expand

---

## Purpose

This document explains how Yuzu works with forest data and generates narratives. Unlike traditional forest monitoring reports that combine dozens of datasets with complex methodologies, Yuzu starts simple and builds incrementally. We document what we actually do, not what we might do someday.

---

## Data Sources

### TBD

---

## Data Processing

### Area Calculations

All area calculations use **geodesic area** accounting for Earth's curvature:
- Pixel area varies from ~900 m² at equator to ~200 m² near poles
- We calculate exact geodesic area per pixel using Earth Engine's built-in methods
- Areas are summed within regions of interest (countries, custom polygons)

### Tree Cover Threshold

By default, we use **30% canopy density threshold**, matching GFW and most forest monitoring literature. This means:
- Pixels with ≥30% tree cover are considered "tree cover"

### Regional Aggregation

Currently, we aggregate data by:
- **Custom polygons:** User-defined regions stored in PostGIS database
- **Administrative boundaries:** Using ISO country codes (future)

No attempt is made to reclassify land use, distinguish natural from planted forests, or infer causality of loss. We report what the satellite data shows.

---

## Database Storage

### Schema Design Philosophy

Our PostgreSQL + PostGIS database stores:
- **Raw metrics from Earth Engine:** tree cover area, loss by year, gain total
- **Calculated derived metrics:** percent loss, annual rates
- **Spatial geometries:** Regions of interest as PostGIS polygons
- **Metadata:** Data extraction timestamps, source dataset versions

**What we don't invent:**
- No "current forest cover" calculations (requires assumptions about gain/loss overlap)
- No land-use classifications beyond what source data provides
- No interpolation or gap-filling
- No predictive modeling

If a metric can't be directly computed from data, we don't store it.

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

- How much tree canopy was lost in a region, by year
- How loss rates are changing over time
- Comparative rankings (which regions lost most)
- Trends over the dataset timespan (?-current)

### What Yuzu Cannot Tell You

- **Why loss occurred:** Fire, logging, agriculture, natural disturbance? Currently out of scope of our data we collect
- **Current forest cover:** There is no reliable way to combine loss and gain data to infer current cover
- **Forest quality or biodiversity:** Tree cover is one-dimensional
- **Socioeconomic impacts:** We don't model human displacement, economic costs, carbon markets, etc. (yet)
- **Future projections:** We report historical data, not predictions

### The LLM Uncertainty Factor

**LLMs introduce a new kind of limitation:**
- **Plausible-sounding errors:** Models can generate statistically fluent text that contains subtle inaccuracies
- **Contextual drift:** Longer narratives may lose grounding in data
- **Cultural/political bias:** Models trained on internet text carry embedded biases
- **Hallucination risk:** Despite validation, some invented details may slip through

**Our mitigation strategy:**
- Strict fact-grounding validation (every number must be traceable)
- Short narrative formats reduce drift
- Human review of samples (at least 10% of generated content)
- Transparent labeling: readers know narratives are AI-generated

**We are experimenting with AI journalism.** Mistakes will happen. When they do, we'll document them and improve the process.

---

## Quality Assurance

### Data Pipeline Validation

- **Automated tests:** Every data extraction includes sanity checks (e.g., loss can't exceed 2000 baseline)
- **Comparison to GFW:** Spot-check our calculated totals against Global Forest Watch dashboard
- **Version tracking:** Log Earth Engine dataset version for each extraction

### Narrative Validation

- **Human review** of all narratives before publication
- **User feedback loop** Readers can flag suspect claims
- **Prose quality, readability, emotional impact** (subjective)

### What We Don't Validate (Yet)

- Cultural appropriateness of framing (requires domain expertise)
- Deep fact-checking beyond numeric claims (e.g., historical context)

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

- Hansen, M. C., et al. (2013). High-resolution global maps of 21st-century forest cover change. *Science*, 342(6160), 850-853. [https://doi.org/10.1126/science.1244693](https://doi.org/10.1126/science.1244693)
- Tyukavina, A., et al. (2022). Global trends of forest loss due to fire from 2001 to 2019. *Frontiers in Remote Sensing*, 3. [https://doi.org/10.3389/frsen.2022.825190](https://doi.org/10.3389/frsen.2022.825190)
- Global Forest Watch. [https://www.globalforestwatch.org/](https://www.globalforestwatch.org/)
- Google Earth Engine Data Catalog: Hansen Global Forest Change. [https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11)

---

## Contact

Questions about methodology? Found an error? Create a github issue.

This is a hobby project exploring AI-powered data storytelling. We welcome critique, skepticism, and suggestions.
