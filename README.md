# 🍋 Yuzu — A Living Chronicle of the World's Forests

## 🌱 Overview & Motivation

**Yuzu** is an open-source experiment in environmental storytelling — a data pipeline that listens to forests through satellite data, then retells what it hears as evolving, human-readable stories.

Instead of dashboards or static reports, Yuzu produces *chronicles*: daily or weekly narrative entries that describe how a forest's canopy, rainfall, and fire activity are changing.
It aims to combine **climate data science**, **software craftsmanship**, and **creative writing** into one unified system — where code gives nature a voice.

### 🎯 Objectives

* Turn satellite and climate data into **legible, emotional, narrative artifacts**.
* Explore how **LLMs can serve as translators between data and human language**.
* Build a modular, transparent data-to-story pipeline usable by researchers, artists, and educators.
* Serve as a **long-term learning project** in geospatial and data-driven storytelling.

---

## 🌍 Core Concept

Yuzu continuously collects open geospatial data about forest health — canopy loss, fire events, rainfall anomalies, vegetation vigor — and synthesizes them into a story entry.

Each forest (e.g., Amazon, Borneo, Congo Basin) has its own timeline of prose and imagery.

> **June 4, 2025 — Pará, Brazil**
>
> 1.8 km² of forest vanished this month — 10% above the regional average.
> Satellite fire alerts bloomed after a dry spell that lasted eleven days.
>
> *"The forest whispered in smoke again, waiting for rain."*

---

## 🪞 Project Philosophy

1. **Truth first, poetry second.** Stories are grounded in data, never fabricated.
2. **Machine as interpreter, not author.** The LLM translates numbers into language; it doesn't invent events.
3. **Transparency over magic.** Every sentence can be traced back to measurable data.
4. **Beauty through structure.** Pipelines and prose are both crafted systems.

NB: I'm using copilot extensively, feel free to report any hallucinations or mistakes

---

## 🗺️ Data Sources

| Dataset               | Provider           | Format        | Purpose                                              |
|-----------------------|--------------------|---------------|------------------------------------------------------|
| Global Forest Watch   | Hansen et al., UMD | CSV / GeoTIFF | Annual canopy loss/gain per 30 m pixel               |
| Copernicus Sentinel-2 | ESA                | GeoTIFF       | NDVI vegetation index                                |
| NASA FIRMS            | NASA               | CSV / API     | Active fires and thermal anomalies                   |
| ERA5 / CHIRPS         | Copernicus CDS     | NetCDF        | Rainfall and temperature anomalies                   |
| ESA CCI Land Cover    | ESA                | NetCDF        | Land-use classes (forest, cropland, grassland, etc.) |

All data are open and programmatically accessible.

---

## 🧰 Technology Stack

| Layer                         | Technologies                                                  | Purpose                                        |
|-------------------------------|---------------------------------------------------------------|------------------------------------------------|
| **Language**                  | Python 3.12                                                   | Core implementation language                   |
| **Package Manager**           | Poetry 2.2.1                                                  | Dependency management and virtual environments |
| **Ingestion & Orchestration** | Prefect / Airflow                                             | Schedule and automate data pulls               |
| **Data Processing**           | Pandas, GeoPandas, xarray, Rasterio, Shapely                  | Handle raster/vector data and compute metrics  |
| **Storage**                   | PostgreSQL 16 + PostGIS 3.4 + TimescaleDB                     | Persist spatial and temporal datasets          |
| **ORM**                       | SQLAlchemy 2.0 + GeoAlchemy2                                  | Database abstraction layer                     |
| **Story Generation**          | Abstract LLM interface (provider-agnostic) + Jinja2 templates | Transform numeric metrics into narrative prose |
| **Visualization**             | Streamlit / Plotly / Folium / Matplotlib                      | Map layers, charts, and timelines              |
| **Code Quality**              | Ruff (linting + formatting), mypy (type checking)             | Enforce code standards and type safety         |
| **Testing**                   | pytest + pytest-cov                                           | Unit and integration testing                   |
| **Config**                    | Pydantic Settings + python-dotenv                             | Type-safe configuration management             |
| **Infrastructure**            | Docker Compose, GitHub Actions                                | Reproducible builds and CI/CD                  |
| **Deployment**                | Render / Railway / Heroku                                     | Hosting the dashboard and API                  |

Optional integrations:

* dbt for metric documentation
* S3 / MinIO for raster storage
* Social-media connectors for automatic story publishing

---

## ✨ Key Features

### Phase 1 — MVP

* Periodic ingestion of deforestation, NDVI, fire, and rainfall data for one or more regions.
* Computation of derived metrics: canopy loss %, NDVI trend, rainfall anomaly, fire density.
* Generation of textual "forest chronicles" via LLM abstraction layer.
* Simple visualization dashboard (Streamlit).
* PostgreSQL / PostGIS / TimescaleDB for historical data storage.

### Phase 2 — Enhanced

* Time-lapse NDVI and fire maps per region.

* Markdown/HTML story archive per forest.

* REST API endpoint:

  `GET /forest/<region>?date=YYYY-MM-DD`
  → returns JSON { loss_pct, ndvi_trend, fire_rate, summary_text }

* Extensible LLM adapter system (e.g., OpenAI, Anthropic, Ollama) via unified interface.

### Phase 3 — Exploratory

* Correlation analyses (e.g., canopy loss vs. rainfall anomaly).
* Biodiversity overlays from GBIF.
* Event-triggered alerts ("forest loss exceeded 10% this quarter").
* Generative visual summaries or AI-composed "forest poems."

---

## 🕒 Suggested Timeline

| Phase      | Duration                                                         | Milestones                                              |
|------------|------------------------------------------------------------------|---------------------------------------------------------|
| Week 1–2   | Setup + first dataset ingestion                                  | Prefect flow, store GFW & FIRMS data in PostGIS         |
| Week 3–4   | Analysis pipeline                                                | Compute canopy-loss %, NDVI trend, rainfall correlation |
| Week 5–6   | Story generation layer                                           | Implement LLM abstraction + Jinja2 templating           |
| Week 7–8   | Visualization & UI                                               | Streamlit dashboard, map layers                         |
| Week 9–10  | API & automation                                                 | REST endpoints, scheduled story publishing              |
| Beyond MVP | Scaling, multiple forests, LLM fine-tuning, open dataset release |                                                         |

---

## 🧱 Project Structure

```
yuzu/
├── src/yuzu/                      # Main application package
│   ├── config.py                  # Pydantic settings (type-safe configuration)
│   ├── pipeline/                  # Data pipeline modules
│   │   ├── ingestion/            # External data fetchers (GFW, FIRMS, etc.)
│   │   ├── processing/           # NDVI, rainfall, fire computations
│   │   ├── db/                   # PostGIS schema, ORM models, connections
│   │   └── orchestration/        # Prefect/Airflow flows
│   ├── storytelling/              # Narrative generation
│   │   ├── templates/            # Jinja2 text structures
│   │   └── llm_interface.py      # Provider-agnostic LLM wrapper
│   └── visualization/             # Dashboards & charts
│       ├── dashboard.py          # Streamlit UI
│       └── maps.py               # Folium / Plotly map renderers
├── tests/                         # Test suite (pytest)
├── data/                          # Data storage
│   ├── raw/                      # Raw datasets
│   └── processed/                # Processed outputs
├── docs/adr/                      # Architecture Decision Records
├── pyproject.toml                 # Poetry config + tool settings (Ruff, mypy, pytest)
├── docker-compose.yml             # PostgreSQL + PostGIS services
├── Dockerfile                     # Application container (Ubuntu + geospatial libs)
├── Makefile                       # Development commands (lint, format, test, etc.)
├── .env                           # Environment variables (local, gitignored)
├── .env.example                   # Environment template
└── README.md
```

---

## 🧪 Example Metrics

| Metric                 | Description                                           |
|------------------------|-------------------------------------------------------|
| canopy_loss_pct        | % loss per region over time (Δ forest pixels / total) |
| ndvi_trend             | NDVI moving-average slope (vegetation health)         |
| fire_density           | Fire events / km² per month                           |
| rainfall_anomaly       | Z-score deviation from 5-year mean                    |
| deforestation_velocity | Rate of change of canopy-loss % over time             |

---

## 🪄 Narrative Generation Logic

The **storytelling subsystem** transforms computed metrics into structured text.
It works in three layers:

1. **Template Selection:** Choose an appropriate template based on detected trends (e.g., loss accelerating vs. recovering).
2. **LLM Summarization:** Pass key metrics and context into the abstracted LLM interface, which returns polished prose.
3. **Styling:** Combine LLM output with standardized phrasing and a short poetic coda.

Example pseudo-prompt:

```
System: You are Yuzu, an impartial yet empathetic observer of forests.
User: Summarize these data in 3 short sentences.
Data: loss_pct=12.4, ndvi_trend=-0.05, rainfall_anomaly=-1.3, fire_density=7/km²
```

Result:

> "In the past season, tree cover shrank by twelve percent, the ground growing brittle beneath scarce rain.
> Fires flickered across dry grasslands, tracing scars where roots once held soil."

---

## 🧭 Design Principles

* **Provider-agnostic AI layer** — compatible with any LLM backend (API key defined in config).
* **Human-verifiable output** — all text tied to traceable metrics.
* **Configurable personality** — tone and style adjustable through templates.
* **Reproducible pipelines** — every story can be regenerated deterministically from data + seed.
* **Low friction for contributors** — simple data folders, modular components.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**: `brew install python@3.12` (macOS) or use your system's package manager
- **Poetry 2.2.1+**: `brew install poetry` or [installation guide](https://python-poetry.org/docs/#installation)
- **Docker Desktop**: [download here](https://www.docker.com/products/docker-desktop)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/yuzu.git
   cd yuzu
   ```

2. **Install dependencies**
   ```bash
   make dev-install
   # or manually: poetry install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database settings
   ```

4. **Start database services**
   ```bash
   make docker-up
   # or: docker compose up -d
   ```
   
   This starts PostgreSQL 16 with PostGIS 3.4 extension and creates the `forest` schema.

5. **Verify setup**
   ```bash
   make all
   # Runs: format, lint, type check, and tests
   ```

### Development Commands

All commands are available via `make`:

```bash
make help          # Show all available commands
make dev-install   # Install all dependencies (including dev tools)
make lint          # Run Ruff linter (check only)
make format        # Format code with Ruff
make type          # Run mypy type checker
make test          # Run pytest tests
make test-cov      # Run tests with coverage report
make all           # Run format, lint, type, and test

make docker-up     # Start PostgreSQL + PostGIS
make docker-down   # Stop Docker services
make docker-logs   # View Docker logs
make db-shell      # Connect to PostgreSQL shell
```

### Configuration

Configuration is managed via `.env` file and loaded using Pydantic Settings for type safety.

**Key settings:**
- `ENVIRONMENT`: `development` | `staging` | `production`
- `POSTGRES_*`: Database connection parameters (user, password, host, port, db)
- `LLM_PROVIDER`: `openai` | `anthropic` | `ollama`
- `LLM_API_KEY`: API key for your chosen LLM provider
- `LLM_MODEL`: Model name (e.g., `gpt-4`, `claude-3-opus-20240229`)

See `.env.example` for all available configuration options.

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report (HTML)
poetry run pytest --cov=src/yuzu --cov-report=html

# Run specific test file
poetry run pytest tests/test_config.py -v
```

Current test coverage: **87%**

### Code Quality

This project uses:
- **Ruff** for linting and formatting (replaces Black, isort, Flake8)
- **mypy** for strict type checking
- **Line length:** 100 characters
- **Type hints:** Required for all functions (strict mode enabled)

Run quality checks on-demand with `make all` (no pre-commit hooks by design to preserve flow).

### Docker Services

**PostgreSQL + PostGIS:**
```bash
# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f postgres

# Connect to database
docker compose exec postgres psql -U yuzu -d yuzu

# Stop services
docker compose down
```

**Optional pgAdmin (database UI):**
```bash
# Start with tools profile
docker compose --profile tools up -d

# Access at: http://localhost:5050
# Credentials: admin@yuzu.local / admin
```

---

## 📦 Future Directions

* Plug-in system for additional environmental datasets (biodiversity, hydrology).
* "Voice packs" — customizable tones (scientific, poetic, journalistic).
* Interactive "forest timeline" UI with scrollable narratives.
* Educational mode for classrooms: simplified text + visualization bundle.
* Publishing pipeline for newsletters, social media, or museum displays.

---

## 📚 References & Inspiration

* Global Forest Watch — [https://data.globalforestwatch.org/](https://data.globalforestwatch.org/)
* NASA FIRMS — [https://firms.modaps.eosdis.nasa.gov/](https://firms.modaps.eosdis.nasa.gov/)
* Copernicus Data Space — [https://dataspace.copernicus.eu/](https://dataspace.copernicus.eu/)
* ESA Climate Change Initiative — [https://climate.esa.int/](https://climate.esa.int/)
* *Art from Space: Satellite Data as Storytelling* — ESA blog series

---

## 🌱 Current Status

**Phase:** Project initialization complete ✅

**Completed:**
- ✅ Python 3.12 + Poetry 2.2.1 setup
- ✅ PostgreSQL 16 + PostGIS 3.4 running in Docker
- ✅ Type-safe configuration with Pydantic Settings
- ✅ Code quality tooling (Ruff, mypy, pytest)
- ✅ Database connection layer with SQLAlchemy
- ✅ Project structure and development workflow
- ✅ 87% test coverage

**Next steps:**
- [ ] Design database schema for forest data
- [ ] Implement data ingestion for Global Forest Watch
- [ ] Set up Prefect for workflow orchestration
- [ ] Create first geospatial processing pipeline
- [ ] Integrate LLM abstraction layer for narrative generation

---

## 📚 Architecture Decisions

Major design decisions are documented in `docs/adr/` following the format `ADR-XXX-short-title.md`.

See [ADR-000: Template](docs/adr/000-template.md) for the standard format.

---

## ✨ Vision Statement

Yuzu listens where satellites only measure.
It translates the cold grammar of pixels into the warm syntax of memory, crafting stories that remind us the Earth is alive, still speaking — if we choose to hear it.

> *"Forests fade in silence. Yuzu remembers their voices."*
