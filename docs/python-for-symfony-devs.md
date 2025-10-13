# 🐍 Python Development Guide for Symfony Developers

## 🎯 Overview

Welcome! This guide helps you transition from PHP/Symfony's OOP and DDD patterns to Python's more **functional-leaning, composition-oriented** style, while still maintaining clean architecture principles you're familiar with.

---

## 🔄 Mental Model Shifts

### From Symfony to Python

| Concept | Symfony/PHP | Python/Yuzu | Key Difference |
|---------|-------------|-------------|----------------|
| **Paradigm** | Heavy OOP, interfaces, abstract classes | Mix of OOP + functional, protocols, duck typing | Python favors **composition over inheritance** |
| **Dependency Injection** | Autowiring, service containers | Explicit passing, factory functions, `@lru_cache` | Less "magic", more explicit |
| **Type Safety** | PHP 8+ strict types | Type hints + mypy (optional at runtime) | Types are for **tooling**, not enforcement |
| **Namespacing** | `\App\Domain\Forest\Service` | `yuzu.pipeline.processing` | Flatter hierarchies, less nesting |
| **Configuration** | YAML/XML service definitions | Pydantic Settings, dataclasses | **Code as config** (Python files) |
| **Testing** | PHPUnit (xUnit style) | pytest (functional style) | Fixtures over setUp/tearDown |
| **Modularity** | Bundles, bounded contexts | Packages, modules, simple folders | Python packages are just directories with `__init__.py` |

---

## 🏗️ Architecture Comparison

### Symfony/DDD Structure
```php
src/
├── Domain/
│   ├── Forest/
│   │   ├── Entity/ForestRegion.php
│   │   ├── Repository/ForestRepositoryInterface.php
│   │   ├── Service/DeforestationCalculator.php
│   │   └── ValueObject/Coordinates.php
│   └── Fire/...
├── Application/
│   ├── UseCase/IngestFireData.php
│   └── DTO/FireEventDTO.php
├── Infrastructure/
│   ├── Persistence/DoctrineForestRepository.php
│   └── ExternalApi/NasaFirmsClient.php
└── Presentation/
    └── Controller/ForestController.php
```

**Characteristics:**
- Deep nesting (4-5 levels)
- Strict layer separation (Domain/Application/Infrastructure)
- Interfaces everywhere
- Heavy use of abstract classes

---

### Python/Yuzu Structure
```python
src/yuzu/
├── pipeline/
│   ├── ingestion/
│   │   ├── gfw.py           # fetch_forest_loss(region, date_range)
│   │   ├── firms.py         # fetch_fire_events(bbox, date)
│   │   └── copernicus.py    # download_sentinel_tile(tile_id)
│   ├── processing/
│   │   ├── ndvi.py          # compute_ndvi_trend(raster_path)
│   │   ├── fire_density.py  # calculate_fire_density(events, area)
│   │   └── canopy_loss.py   # aggregate_loss_by_region(gfw_data)
│   ├── db/
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── connection.py    # Session management
│   │   └── repositories.py  # Optional: data access layer
│   └── orchestration/
│       └── flows.py         # Prefect workflow definitions
├── storytelling/
│   ├── llm.py               # Abstract LLM interface
│   ├── templates.py         # Jinja2 template selection
│   └── generator.py         # generate_chronicle(metrics, region)
└── config.py                # Pydantic Settings
```

**Characteristics:**
- **Flatter hierarchy** (2-3 levels max)
- **Modules as units of organization** (files, not classes)
- Functions > Classes (unless state is needed)
- **Explicit over abstract**

---

## 🧩 Modularization: Python Style

### 1️⃣ **Think in Modules, Not Classes**

In Symfony, you'd create a service class:

```php
// Symfony
class DeforestationCalculator {
    public function __construct(
        private ForestRepositoryInterface $repo,
        private LoggerInterface $logger
    ) {}
    
    public function calculate(ForestRegion $region): float {
        $data = $this->repo->findLossData($region);
        return $this->computeLossPercentage($data);
    }
}
```

In Python, prefer **module-level functions** with dependency injection via parameters:

```python
# yuzu/pipeline/processing/canopy_loss.py
from typing import Protocol
from geopandas import GeoDataFrame
from yuzu.pipeline.db.connection import get_db_session

def calculate_loss_percentage(
    region_id: str,
    start_date: date,
    end_date: date,
) -> float:
    """Calculate canopy loss % for a region.
    
    Args:
        region_id: Geographic identifier
        start_date: Period start
        end_date: Period end
        
    Returns:
        Loss percentage (0-100)
    """
    with get_db_session() as session:
        data = _fetch_loss_data(session, region_id, start_date, end_date)
        return _compute_percentage(data)


def _fetch_loss_data(session: Session, region_id: str, ...) -> GeoDataFrame:
    """Private helper - fetch raw data."""
    # Implementation
    ...

def _compute_percentage(data: GeoDataFrame) -> float:
    """Private helper - compute metric."""
    # Implementation
    ...
```

**Why?**
- **Easier to test** (no need to mock entire objects)
- **Easier to compose** (functions chain naturally)
- **Less boilerplate** (no interface definitions needed)
- **Clear data flow** (inputs → outputs, no hidden state)

---

### 2️⃣ **When to Use Classes**

Use classes when you need:
1. **Stateful objects** (database connections, API clients)
2. **Shared configuration** across methods
3. **Protocols/interfaces** (Python's structural typing)

Example — API Client (stateful):

```python
# yuzu/pipeline/ingestion/firms.py
from typing import Protocol
import httpx
from yuzu.config import get_settings

class FireDataClient:
    """NASA FIRMS API client with authentication."""
    
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_settings().nasa_firms_api_key
        self._client = httpx.Client(
            base_url="https://firms.modaps.eosdis.nasa.gov",
            timeout=30.0,
        )
    
    def fetch_fire_events(
        self,
        bbox: tuple[float, float, float, float],
        date: date,
    ) -> list[dict]:
        """Fetch fire events for bounding box."""
        response = self._client.get(
            "/api/area/csv",
            params={
                "bbox": ",".join(map(str, bbox)),
                "date": date.isoformat(),
                "key": self.api_key,
            },
        )
        response.raise_for_status()
        return self._parse_csv(response.text)
    
    def _parse_csv(self, text: str) -> list[dict]:
        """Parse CSV response."""
        # Implementation
        ...
    
    def close(self) -> None:
        """Close HTTP connection."""
        self._client.close()
```

**Usage:**
```python
# Simple functional wrapper
def fetch_fire_events(bbox, date):
    """Convenience function for one-off fetches."""
    client = FireDataClient()
    try:
        return client.fetch_fire_events(bbox, date)
    finally:
        client.close()
```

---

### 3️⃣ **Protocols Over Interfaces**

Instead of Symfony interfaces, use **Protocols** (structural typing):

```python
# yuzu/pipeline/ingestion/protocols.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class DataFetcher(Protocol):
    """Contract for data ingestion clients."""
    
    def fetch(self, region_id: str, date_range: tuple[date, date]) -> GeoDataFrame:
        """Fetch geospatial data for region."""
        ...
```

Any class implementing this method signature automatically satisfies the protocol — **no explicit inheritance needed** (duck typing).

```python
# Multiple implementations
class GFWFetcher:
    def fetch(self, region_id: str, date_range: tuple[date, date]) -> GeoDataFrame:
        # Global Forest Watch implementation
        ...

class COPERNICUSFetcher:
    def fetch(self, region_id: str, date_range: tuple[date, date]) -> GeoDataFrame:
        # Copernicus implementation
        ...

# Both satisfy DataFetcher protocol without explicit declaration
def process_data(fetcher: DataFetcher, region: str) -> None:
    data = fetcher.fetch(region, (...))  # mypy validates this
```

---

## 🎨 Dependency Injection: Python Way

### Symfony Approach
```yaml
# services.yaml
services:
    App\Service\DeforestationCalculator:
        arguments:
            $repo: '@App\Repository\ForestRepository'
            $logger: '@logger'
```

### Python Approach (Explicit)

**Option 1: Factory functions**
```python
# yuzu/pipeline/processing/factory.py
from yuzu.pipeline.db.connection import get_engine
from yuzu.config import get_settings

def create_canopy_loss_processor():
    """Factory for canopy loss processing."""
    settings = get_settings()
    engine = get_engine()
    return CanopyLossProcessor(
        engine=engine,
        min_confidence=settings.min_confidence,
    )
```

**Option 2: Functional dependencies (preferred for Yuzu)**
```python
# Just pass what you need
def calculate_loss(
    region_id: str,
    date_range: tuple[date, date],
    session: Session,  # Explicit dependency
) -> float:
    """Calculate loss with explicit session dependency."""
    data = session.query(...).filter(...)
    return compute_metric(data)

# Call site
with get_db_session() as session:
    loss = calculate_loss("amazon_north", (start, end), session)
```

**Option 3: Context managers for resources**
```python
# yuzu/pipeline/ingestion/firms.py
from contextlib import contextmanager

@contextmanager
def fire_data_client():
    """Context manager for FIRMS client."""
    client = FireDataClient()
    try:
        yield client
    finally:
        client.close()

# Usage
with fire_data_client() as client:
    events = client.fetch_fire_events(bbox, date)
```

---

## 🧪 Testing: pytest vs PHPUnit

### PHPUnit Style (Class-based)
```php
class DeforestationCalculatorTest extends TestCase {
    private DeforestationCalculator $calculator;
    
    protected function setUp(): void {
        $this->calculator = new DeforestationCalculator(
            $this->createMock(ForestRepository::class),
            $this->createMock(LoggerInterface::class)
        );
    }
    
    public function testCalculatesLoss(): void {
        $result = $this->calculator->calculate($region);
        $this->assertEquals(12.5, $result);
    }
}
```

### pytest Style (Functional)
```python
# tests/test_canopy_loss.py
import pytest
from yuzu.pipeline.processing.canopy_loss import calculate_loss_percentage

@pytest.fixture
def sample_region():
    """Fixture providing test data."""
    return "amazon_test_region"

@pytest.fixture
def mock_session(mocker):
    """Fixture providing mocked database session."""
    return mocker.Mock(spec=Session)

def test_calculates_loss(sample_region, mock_session):
    """Test loss calculation."""
    # Arrange
    mock_session.query.return_value.filter.return_value.all.return_value = [...]
    
    # Act
    result = calculate_loss_percentage(
        region_id=sample_region,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    
    # Assert
    assert result == pytest.approx(12.5, abs=0.1)

def test_handles_empty_data(sample_region, mock_session):
    """Test behavior with no data."""
    mock_session.query.return_value.filter.return_value.all.return_value = []
    
    result = calculate_loss_percentage(sample_region, ...)
    
    assert result == 0.0
```

**Key differences:**
- **Fixtures instead of setUp/tearDown** (more composable)
- **Functions over methods** (no inheritance needed)
- **Parametrize for multiple cases** (DRY testing)

```python
@pytest.mark.parametrize("loss_pct,expected", [
    (0.0, "stable"),
    (5.0, "moderate"),
    (15.0, "severe"),
])
def test_loss_classification(loss_pct, expected):
    assert classify_loss(loss_pct) == expected
```

---

## 📦 Package Structure: Bounded Contexts in Python

### DDD Bounded Context (Symfony)
```
src/Forest/          # Forest Context
src/Fire/            # Fire Context
src/Climate/         # Climate Context
```

Each context has Domain/Application/Infrastructure.

### Python Equivalent (Yuzu)
```python
src/yuzu/
├── pipeline/        # Data Pipeline Context
│   ├── ingestion/   # Submodule: data sources
│   ├── processing/  # Submodule: metrics
│   └── db/          # Submodule: persistence
├── storytelling/    # Narrative Context
└── visualization/   # Presentation Context
```

**Within a context, organize by feature:**
```python
# pipeline/processing/
├── __init__.py
├── ndvi.py          # NDVI-related functions
├── fire_density.py  # Fire-related functions
├── canopy_loss.py   # Canopy-related functions
└── common.py        # Shared utilities
```

**Not by layer:**
```python
# ❌ Avoid this (too much nesting)
processing/
├── services/
├── repositories/
├── value_objects/
└── entities/
```

---

## 🔧 Configuration: Code > YAML

### Symfony
```yaml
# config/services.yaml
parameters:
    app.nasa_api_key: '%env(NASA_API_KEY)%'
    app.min_confidence: 0.8
```

### Python (Pydantic Settings)
```python
# yuzu/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Type-safe configuration."""
    
    nasa_api_key: str = Field(..., description="NASA FIRMS API key")
    min_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    model_config = SettingsConfigDict(env_file=".env")

# Usage
from yuzu.config import get_settings

settings = get_settings()
api_key = settings.nasa_api_key  # Autocomplete works!
```

**Benefits:**
- **Type hints** (IDE autocomplete)
- **Validation** (Pydantic checks constraints)
- **No parsing** (Python evaluates directly)
- **Documentation** (Field descriptions)

---

## 🎯 Yuzu-Specific Patterns

### 1️⃣ **Pipeline as Functions**

Think of each pipeline stage as a **pure function** (input → output):

```python
# Symfony mindset: chained services
$processor = $container->get(DataProcessor::class);
$result = $processor->ingest()->transform()->analyze()->store();

# Python mindset: composed functions
from yuzu.pipeline import ingestion, processing, db

def run_forest_analysis_pipeline(region: str, date: date) -> dict:
    """Orchestrate the full pipeline."""
    # 1. Ingest
    raw_data = ingestion.fetch_gfw_data(region, date)
    fire_events = ingestion.fetch_firms_data(region, date)
    
    # 2. Process
    loss_pct = processing.calculate_loss_percentage(raw_data)
    fire_density = processing.calculate_fire_density(fire_events)
    
    # 3. Store
    with db.get_db_session() as session:
        db.save_metrics(session, region, date, loss_pct, fire_density)
    
    # 4. Return
    return {"loss_pct": loss_pct, "fire_density": fire_density}
```

### 2️⃣ **Repository Pattern (Optional)**

You CAN use repositories in Python, but they're less essential:

```python
# yuzu/pipeline/db/repositories.py
from sqlalchemy.orm import Session
from yuzu.pipeline.db.models import ForestMetric

class ForestMetricRepository:
    """Repository for forest metrics."""
    
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def find_by_region(self, region_id: str) -> list[ForestMetric]:
        return self.session.query(ForestMetric).filter_by(region_id=region_id).all()
    
    def save(self, metric: ForestMetric) -> None:
        self.session.add(metric)

# Usage
with get_db_session() as session:
    repo = ForestMetricRepository(session)
    metrics = repo.find_by_region("amazon_north")
```

**But often simpler to just:**
```python
def get_metrics_by_region(session: Session, region_id: str) -> list[ForestMetric]:
    """Query metrics for region."""
    return session.query(ForestMetric).filter_by(region_id=region_id).all()
```

### 3️⃣ **Value Objects → Dataclasses**

Symfony Value Objects:
```php
final class Coordinates {
    public function __construct(
        private float $latitude,
        private float $longitude
    ) {
        // Validation
    }
}
```

Python Dataclasses:
```python
from dataclasses import dataclass
from typing import Annotated
from pydantic import Field, BaseModel

# Option 1: Standard dataclass (lightweight)
@dataclass(frozen=True)  # Immutable
class Coordinates:
    latitude: float
    longitude: float

# Option 2: Pydantic model (with validation)
class Coordinates(BaseModel):
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    
    model_config = {"frozen": True}  # Immutable

# Usage
coords = Coordinates(latitude=52.5, longitude=13.4)
```

---

## 🚀 Best Practices Summary

### ✅ Do This
- **Favor functions over classes** (unless you need state)
- **Keep modules flat** (2-3 levels max)
- **Pass dependencies explicitly** (no hidden globals)
- **Use type hints everywhere** (mypy strict mode)
- **Use dataclasses/Pydantic for data** (not primitive obsession)
- **Test at function level** (easier to mock)
- **Use context managers for resources** (`with` statements)
- **Embrace duck typing** (Protocols > inheritance)

### ❌ Avoid This
- Deep inheritance hierarchies
- Over-abstracting with interfaces
- Service containers / global registries
- Massive classes with many methods
- Mixing business logic with I/O
- Mocking entire objects (mock at boundary)

---

## 🔮 Practical Example: Full Feature

**Feature:** Ingest fire data and compute density

### Symfony Approach (5 files)
```
src/Domain/Fire/Entity/FireEvent.php
src/Domain/Fire/Repository/FireEventRepositoryInterface.php
src/Domain/Fire/Service/FireDensityCalculator.php
src/Infrastructure/Persistence/DoctrineFireEventRepository.php
src/Infrastructure/ExternalApi/NasaFirmsClient.php
```

### Python Approach (2 files)

**File 1: `yuzu/pipeline/ingestion/firms.py`**
```python
"""NASA FIRMS data ingestion."""
import httpx
from datetime import date
from yuzu.config import get_settings

def fetch_fire_events(
    bbox: tuple[float, float, float, float],
    target_date: date,
) -> list[dict]:
    """Fetch fire events from NASA FIRMS API.
    
    Args:
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        target_date: Date to query
        
    Returns:
        List of fire events with lat/lon/brightness
    """
    settings = get_settings()
    response = httpx.get(
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv",
        params={
            "bbox": ",".join(map(str, bbox)),
            "date": target_date.isoformat(),
            "key": settings.nasa_firms_api_key,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return _parse_csv_response(response.text)

def _parse_csv_response(csv_text: str) -> list[dict]:
    """Parse FIRMS CSV format."""
    # Implementation
    ...
```

**File 2: `yuzu/pipeline/processing/fire_density.py`**
```python
"""Fire density calculation."""
from typing import TypedDict

class FireEvent(TypedDict):
    latitude: float
    longitude: float
    brightness: float

def calculate_fire_density(
    events: list[FireEvent],
    area_km2: float,
) -> float:
    """Calculate fire events per km².
    
    Args:
        events: List of fire events
        area_km2: Total area in square kilometers
        
    Returns:
        Fire density (events/km²)
    """
    if area_km2 <= 0:
        raise ValueError("Area must be positive")
    
    return len(events) / area_km2

def calculate_high_intensity_ratio(events: list[FireEvent]) -> float:
    """Calculate ratio of high-intensity fires.
    
    High intensity defined as brightness > 330K.
    """
    if not events:
        return 0.0
    
    high_intensity = sum(1 for e in events if e["brightness"] > 330)
    return high_intensity / len(events)
```

**Usage:**
```python
# In orchestration/workflow
from yuzu.pipeline.ingestion.firms import fetch_fire_events
from yuzu.pipeline.processing.fire_density import calculate_fire_density

def analyze_fire_activity(region_bbox, date, area_km2):
    events = fetch_fire_events(region_bbox, date)
    density = calculate_fire_density(events, area_km2)
    return density
```

---

## 📚 Further Reading

- **Effective Python** by Brett Slatkin — Python idioms
- **Fluent Python** by Luciano Ramalho — Advanced patterns
- **Architecture Patterns with Python** by Percival & Gregory — DDD in Python
- **pytest documentation** — Testing patterns

---

## 🎓 TL;DR for Symfony Devs

1. **Classes → Functions** (mostly)
2. **Interfaces → Protocols** (structural typing)
3. **Service Container → Explicit passing** (or factory functions)
4. **Deep nesting → Flat modules** (by feature, not layer)
5. **setUp/tearDown → Fixtures** (pytest)
6. **YAML config → Pydantic** (type-safe, validated)
7. **Think pipelines, not services** (data flows through functions)

**Core philosophy:** Python favors **simplicity, explicitness, and composition** over elaborate OOP hierarchies. You'll write less boilerplate but need to be more intentional about structure.

Welcome to Yuzu! 🍋

