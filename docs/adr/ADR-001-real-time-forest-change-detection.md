# ADR-001: Choosing a Primary Forest Data Source

**Date:** 2025-10-27  
**Status:** Draft  
**Authors:** Kacper Wojtaszczyk & AI Copilot

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

**Philosophy**: Start simple. Find one dataset we can rely on. Build from there. Resist the temptation to merge multiple inconsistent sources just to fill data gaps.

---

## Candidate Data Sources

### [PLACEHOLDER: Source 1 Name]

**Summary:** [Brief description]

**Access:**
- API/SDK: [Details]
- Documentation: [Quality assessment]
- Rate limits: [If applicable]

**Data characteristics:**
- **Temporal coverage:** [Date range]
- **Update frequency:** [How often]
- **Spatial resolution:** [Pixel size]
- **Geographic coverage:** [Global/tropical/specific regions]
- **Metrics provided:** [What you actually get]

**Developer experience:**
- [How pleasant is it to work with?]
- [Any gotchas or friction points?]

**Pros:**
- [List specific advantages]

**Cons:**
- [List specific limitations]

**Best for:** [Use case]  
**Worst for:** [Use case]

---

### [PLACEHOLDER: Source 2 Name]

**Summary:** [Brief description]

**Access:**
- API/SDK: [Details]
- Documentation: [Quality assessment]
- Rate limits: [If applicable]

**Data characteristics:**
- **Temporal coverage:** [Date range]
- **Update frequency:** [How often]
- **Spatial resolution:** [Pixel size]
- **Geographic coverage:** [Global/tropical/specific regions]
- **Metrics provided:** [What you actually get]

**Developer experience:**
- [How pleasant is it to work with?]
- [Any gotchas or friction points?]

**Pros:**
- [List specific advantages]

**Cons:**
- [List specific limitations]

**Best for:** [Use case]  
**Worst for:** [Use case]

---

### [PLACEHOLDER: Source 3 Name]

**Summary:** [Brief description]

**Access:**
- API/SDK: [Details]
- Documentation: [Quality assessment]
- Rate limits: [If applicable]

**Data characteristics:**
- **Temporal coverage:** [Date range]
- **Update frequency:** [How often]
- **Spatial resolution:** [Pixel size]
- **Geographic coverage:** [Global/tropical/specific regions]
- **Metrics provided:** [What you actually get]

**Developer experience:**
- [How pleasant is it to work with?]
- [Any gotchas or friction points?]

**Pros:**
- [List specific advantages]

**Cons:**
- [List specific limitations]

**Best for:** [Use case]  
**Worst for:** [Use case]

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
