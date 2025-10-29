# ADR-002: Library-first architecture with a thin FastAPI API added later

Date: 2025-10-29
Status: Proposed
Author: AI Copilot (with Kacper)

---

## 🧠 Context

Yuzu is primarily a data pipeline and storytelling system: ingest geospatial data, compute metrics, and generate narratives. A web/API surface will be useful later to feed a React frontend, but current scope prioritizes ingestion, processing, and LLM-based narrative generation.

Constraints and priorities:
- Keep core logic framework-agnostic and easy to test.
- Strong geospatial + PostGIS posture (SQLAlchemy 2.0 + GeoAlchemy2).
- Reproducibility and type safety (pytest + pytest-cov, mypy strict, Ruff lint/format) — already configured in pyproject.toml and Makefile.
- Defer web complexity until needed; when added, it will be a simple JSON API, no auth initially.
- Dockerized Postgres/PostGIS environment is available; migrations not yet set up.

---

## 🔄 Alternatives Considered

### Option A — Django “batteries-included” now

Summary:
Adopt Django as the overarching framework (settings, routing, ORM, migrations, admin) and develop pipeline within Django app structure.

Pros:
- High velocity for CRUD/admin; many conventions and integrations.
- Built-in ORM and migrations; mature ecosystem.
- Admin UI for quick inspection.

Cons:
- Heavier framework cost without immediate web needs.
- Tighter coupling of pipeline to web framework; harder to keep library boundaries.
- Async/data-pipeline ergonomics less natural compared to modern micro stacks.

Best for: product-first web apps needing admin + auth day one.
Worst for: library-first data pipelines where the web layer is deferred.

---

### Option B — FastAPI service now (API-first)

Summary:
Stand up FastAPI immediately, build domain logic inside the service, and expose endpoints as the primary surface.

Pros:
- Great DX, type-driven schemas (Pydantic), OpenAPI for free.
- Natural fit for JSON API feeding a React frontend.
- Easy to integrate with SQLAlchemy and async HTTP clients.

Cons:
- Encourages domain logic to accumulate inside the service if not disciplined.
- Adds operational footprint (server, deployment, CORS) before it’s needed.
- Geospatial libs are mostly sync; mixing async prematurely adds complexity.

Best for: API-centric services needed early.
Worst for: pipeline-centric R&D where API is last-mile.

---

### Option C — Library/CLI first, thin API later (chosen)

Summary:
Keep Yuzu as a composable Python library and CLI for ingestion/processing/storytelling. Add a separate FastAPI service later that imports the library and exposes JSON endpoints.

Pros:
- Clean separation of concerns; domain stays framework-agnostic and testable.
- Minimal cognitive/ops load until API is justified.
- Easy to integrate with orchestration tools (Prefect/Dagster) without web coupling.

Cons:
- Requires discipline to define stable library boundaries and contracts.
- Some rework when introducing migrations (Alembic) and API module.
- Later integration work (CORS, deployment) becomes a separate mini-project.

Best for: data-centric projects with deferred UI/API.
Worst for: teams needing an admin/UI immediately.

---

## ✅ Decision

Chosen option: C — Library-first, add a thin FastAPI API later.

Rationale:
- Matches current scope and sequencing (ingestion → processing → LLM → API last).
- Preserves modularity and testability (pytest, mypy, Ruff already in place) and keeps geospatial dependencies isolated from web concerns.
- Keeps DB layer (SQLAlchemy + GeoAlchemy2) reusable from scripts, orchestrators, and future API. We will introduce Alembic migrations once the initial schema stabilizes.

Assumptions:
- The first API will be read-mostly, JSON-only, no auth; a React frontend will consume it.
- PostGIS-backed metrics and generated narratives can be computed offline and served quickly.
- Orchestration (Prefect or Dagster) may be adopted when cron/scripts become brittle, without changing the domain/library.

Complexity estimate: Low now; Medium later when adding migrations + API module.
Expected lifespan: Medium-to-long term; revisitable after the first public API.

---

## ⚙️ Consequences

Positive outcomes:
- Core pipeline remains framework-agnostic and simple to test and run locally/CI.
- Quality gates (Ruff, mypy, pytest, coverage) continue to apply uniformly; no web server required for most tests.
- API deployment can be an independent process/service with minimal coupling, easing ops.

Risks / future concerns:
- Boundary drift: ensure API imports only the library surface, not internal modules.
- Data model evolution: add Alembic early enough to avoid manual SQL drift; ensure reproducible migrations.
- CORS and versioning: plan CORS policy and URL versioning once the API is added.

Monitoring triggers (revisit this ADR if):
- We need authentication/authorization or multi-tenant concerns.
- The library boundary becomes leaky or hard to maintain.
- Operational needs (SLAs, scaling) argue for a more integrated framework.

---

## 🧪 Minimal plan and contracts

No code changes now. Prepare the following to de-risk later work:

- Define lightweight library boundaries:
  - yuzu.pipeline.* (ingestion, processing, db, orchestration wrappers)
  - yuzu.storytelling.* (templates, LLM adapter)
  - Small, typed result objects for metrics and narratives (Pydantic models) living outside any web framework.

- Migrations:
  - Adopt Alembic once the first tables are stable; store migrations in a top-level alembic/ directory; enforce reproducible, idempotent migrations.

- Orchestration:
  - Keep flows/scripts separate from the API; orchestrator imports the same library surface as the API.

- API (later), separate module, tentative path: yuzu.api
  - Framework: FastAPI (async-capable, OpenAPI by default).
  - Dependency wiring: inject a session factory and settings; avoid global state.
  - CORS: permissive for the initial React app; tighten later as needed.

Minimal initial endpoint contract (JSON-only, no auth):
- GET /forest/{region}?date=YYYY-MM-DD
  - Response (example):
    {
      "region": "para-br",
      "date": "2025-06-04",
      "metrics": {
        "canopy_loss_pct": 1.8,
        "ndvi_trend": -0.05,
        "fire_density_per_km2": 7,
        "rainfall_anomaly_z": -1.3
      },
      "summary_text": "…short narrative…",
      "sources": ["GLAD", "RADD", "FIRMS", "ERA5"],
      "seed": 42
    }

- Versioning: start at /v1/…; include a simple healthcheck at /health.

---

## 🧰 Tooling alignment (current state)

- Code quality: Ruff (lint + format), mypy strict, pytest + pytest-cov — already configured in pyproject.toml and Makefile targets (format, lint, type, test, test-cov, all).
- Packaging: Poetry (pyproject.toml), Python 3.12, src/ layout.
- Infra: Docker Compose for Postgres + PostGIS; Make targets for docker-up/down/logs and db-shell.
- No web or migrations dependencies yet — this ADR defers them until needed.

---

## 📝 Follow-ups

- Define first-cut Pydantic models for public metrics/narrative payloads in a framework-agnostic module (no FastAPI dependency).
- Draft DB schema and add Alembic when tables stabilize.
- When ready for API:
  - Add optional dependencies: fastapi, uvicorn, httpx (for client tests), and alembic.
  - Create yuzu/api with a small FastAPI app, wire CORS, and expose the endpoint above.
  - Add integration tests that run with a temporary DB/container using existing Makefile workflows.

---

## 🧠 Notes & References

- SQLAlchemy 2.0 + GeoAlchemy2 (current codebase)
- Ruff, mypy, pytest-cov config in pyproject.toml; Makefile commands for quality gates
- Docker Compose for PostGIS; tests for DB connection already in place
- FastAPI docs: dependency injection and Pydantic models
- Alembic for migrations (deferred until schema stabilizes)

