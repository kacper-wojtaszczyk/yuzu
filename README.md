# 🍋 Yuzu — A Living Chronicle of the World's Forests

> ⚠️ **PROJECT STATUS: ON HOLD**  
> After prototyping forest data pipelines, I discovered [WRI's project-zeno](https://github.com/wri/project-zeno) already solves many of the core challenges I was tackling. Rather than reinvent the wheel, **I'm now contributing to project-zeno** with experimental narrative tools.
> 
> **Active work continues here:** [kacper-wojtaszczyk/project-zeno](https://github.com/kacper-wojtaszczyk/project-zeno)  
> Focus: Adding creative narrative experiments (haiku, soundscapes, speculative fiction) to Global Nature Watch's agent.
>
> This repository remains as **research documentation** — see [ADR-001](docs/adr/ADR-001-real-time-forest-change-detection.md) for the full story of exploration and pivot decision.

---

## 🌱 Original Vision

**Yuzu** was an open-source experiment in environmental storytelling — a data pipeline that listens to forests through satellite data, then retells what it hears as evolving, human-readable stories.

Instead of dashboards or static reports, Yuzu aimed to produce *chronicles*: **weekly narrative entries** that describe how a forest's canopy, rainfall, and fire activity are changing.

### 🎯 What We Learned

Through prototyping with Google Dynamic World, we discovered:
- **44.4% volatility** from seasonal phenology makes weekly monitoring challenging
- **No threshold or aggregation method** fully separates deforestation from natural cycles
- **Data pipeline complexity** is substantial (cloud coverage, seasonality, baselines)
- **WRI's project-zeno** already handles these complexities in production

See [ADR-001](docs/adr/ADR-001-real-time-forest-change-detection.md) for detailed experimental results.

### 🎯 The Pivot

Rather than building standalone infrastructure, I'm now:
- **Forking project-zeno** to experiment with narrative formats
- **Adding creative tools** (poetry, audio, speculative fiction) to their agent
- **Learning from production code** rather than reinventing
- **Building portfolio** relevant to conservation tech careers

**Current experimental work:** [kacper-wojtaszczyk/project-zeno](https://github.com/kacper-wojtaszczyk/project-zeno)

---

## 📚 Research Artifacts

This repository preserves valuable learning from the exploration phase:

### Google Dynamic World Prototype
- **Location:** `src/yuzu/pipeline/orchestration/extract_forest_metrics.py`
- **Key Finding:** 44.4% volatility from seasonal phenology
- **Tested:** Multiple thresholds (0.1-0.8), gap-filling strategies, label-based classification
- **Conclusion:** Single-source approach insufficient for weekly monitoring

### Documentation
- **[ADR-001](docs/adr/ADR-001-real-time-forest-change-detection.md):** Complete decision record including:
  - Evaluation of 3 data sources (Dynamic World, GFW Alerts, Custom ML)
  - Experimental results and root cause analysis
  - Pivot decision rationale
  - Future roadmap with project-zeno fork

- **[Methodology](docs/methodology.md):** Universal principles for forest data narratives

- **[Copilot Instructions](docs/project-zeno-fork-copilot-instructions.md):** Comprehensive guide for narrative experiments in project-zeno fork

### Testing Infrastructure
- Earth Engine authentication patterns
- PostgreSQL test setup
- pytest configurations
- Mock data patterns for geospatial testing

---

## 🚀 Active Development

The narrative experimentation continues in my project-zeno fork:

**Repository:** [kacper-wojtaszczyk/project-zeno](https://github.com/kacper-wojtaszczyk/project-zeno)

**Planned Narrative Tools:**
- 🖊️ **Haiku Generator** — 5-7-5 syllable poetic narratives
- 🎵 **Soundscape Generator** — Audio representations of forest change
- 📖 **Speculative Fiction** — "What if" narratives and counterfactuals
- 🌍 **Parallel Earths** — Alternate timeline visualizations
- 🎨 **Image Generation** — Visual storytelling (stretch goal)

**Upstream Project:**
- [WRI project-zeno](https://github.com/wri/project-zeno) — Global Nature Watch AI agent
- [Global Nature Watch](https://globalnaturewatch.org) — Production chatbot
- [Global Forest Watch](https://globalforestwatch.org) — Data source

---

## 📖 Using This Research

If you're exploring forest data pipelines or narrative generation:

1. **Read [ADR-001](docs/adr/ADR-001-real-time-forest-change-detection.md)** for data source evaluation
2. **Check the prototype code** in `src/yuzu/pipeline/orchestration/`
3. **Review [methodology.md](docs/methodology.md)** for universal narrative principles
4. **Consider project-zeno** if you need production-ready infrastructure

---

## 🙏 Acknowledgments

- **WRI (World Resources Institute)** for project-zeno and Global Forest Watch
- **Google Earth Engine** for accessible geospatial computing
- **GLAD/UMD** for forest monitoring datasets (DIST-ALERT, deforestation alerts)
- **NASA** for OPERA project and open satellite data

---

## 📄 License

MIT License — See [LICENSE](LICENSE) file for details.

**Note:** This project is educational/research. The active narrative experiments continue in the [project-zeno fork](https://github.com/kacper-wojtaszczyk/project-zeno).
