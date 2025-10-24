"""Hansen/UMD Global Forest Change baseline data extraction.

This module provides functions for extracting annual forest loss data from the
Hansen et al. Global Forest Change dataset (v1.12, 2000-2024) via Google Earth Engine.

All functions require an initialized EarthEngineContext (see earth_engine.py).
"""

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import ee
import pandas as pd

from yuzu.config import Settings, get_settings
from yuzu.pipeline.ingestion.earth_engine import EarthEngineContext

if TYPE_CHECKING:
    from ee.geometry import Geometry
    from ee.image import Image

logger = logging.getLogger(__name__)


@dataclass
class RegionExtraction:
    """Parameters for extracting forest loss data for a region.

    Attributes:
        region_id: Unique identifier for the region
        region_name: Human-readable region name
        geometry: GeoJSON geometry dict (must be in WGS84/EPSG:4326)
        start_year: First year to extract (inclusive)
        end_year: Last year to extract (inclusive)
        tree_cover_threshold: Min % canopy cover to qualify as forest (None = use config default)
    """

    region_id: str
    region_name: str
    geometry: dict[str, Any]
    start_year: int
    end_year: int
    tree_cover_threshold: int | None = None

    def __post_init__(self) -> None:
        """Validate parameters and apply defaults."""
        if self.tree_cover_threshold is None:
            settings = get_settings()
            self.tree_cover_threshold = settings.tree_cover_threshold

        if not 2000 <= self.start_year <= self.end_year:
            raise ValueError(f"Invalid year range: {self.start_year}-{self.end_year}")

        if not 0 <= self.tree_cover_threshold <= 100:
            raise ValueError(
                f"Tree cover threshold must be 0-100%, got {self.tree_cover_threshold}"
            )


def extract_region(params: RegionExtraction, ee_context: EarthEngineContext) -> pd.DataFrame:
    """Extract annual forest loss data for a region.

    This function:
    1. Calculates year 2000 baseline forest area once
    2. Iterates through specified years, calculating loss per year
    3. Returns a DataFrame with annual loss metrics

    Args:
        params: Region extraction parameters
        ee_context: Initialized Earth Engine context

    Returns:
        DataFrame with columns:
            - region_id: str
            - region_name: str
            - year: int
            - loss_km2: float (forest loss area in km²)
            - baseline_cover_km2: float (year 2000 forest area, same for all rows)
            - tree_cover_threshold: int (threshold used)
            - dataset_version: str (Hansen dataset version)

    Raises:
        RuntimeError: If GEE computation fails after retries

    Example:
        >>> from yuzu.pipeline.ingestion.earth_engine import initialize_earth_engine
        >>> ee_ctx = initialize_earth_engine()
        >>> params = RegionExtraction(
        ...     region_id="test-region",
        ...     region_name="Test Protected Area",
        ...     geometry=geojson_dict,
        ...     start_year=2023,
        ...     end_year=2024
        ... )
        >>> df = extract_region(params, ee_ctx)
    """
    logger.info(
        f"Extracting GFW baseline for {params.region_name} ({params.start_year}-{params.end_year})"
    )

    region = ee.Geometry(params.geometry)  # type: ignore[attr-defined]
    hansen = ee_context.hansen
    settings = ee_context.settings

    # Calculate year 2000 baseline once
    # tree_cover_threshold is guaranteed to be int after __post_init__
    assert params.tree_cover_threshold is not None
    baseline_km2 = _calculate_baseline(region, params.tree_cover_threshold, hansen, settings)
    logger.info(
        f"Year 2000 baseline: {baseline_km2:.2f} km² (threshold: {params.tree_cover_threshold}%)"
    )

    # Extract loss by year
    results = []
    for year in range(params.start_year, params.end_year + 1):
        loss_km2 = _calculate_loss_for_year(region, year, hansen, settings)
        logger.debug(f"Year {year}: {loss_km2:.3f} km² loss")

        results.append(
            {
                "region_id": params.region_id,
                "region_name": params.region_name,
                "year": year,
                "loss_km2": loss_km2,
                "baseline_cover_km2": baseline_km2,
                "tree_cover_threshold": params.tree_cover_threshold,
                "dataset_version": settings.hansen_dataset_version,
            }
        )

    df = pd.DataFrame(results)
    logger.info(
        f"Extracted {len(df)} years. Total loss: {df['loss_km2'].sum():.2f} km² "
        f"({df['loss_km2'].sum() / baseline_km2 * 100:.2f}% of baseline)"
    )
    return df


def _calculate_baseline(
    region: "Geometry", threshold: int, hansen: "Image", settings: Settings
) -> float:
    """Calculate year 2000 forest area in km².

    Args:
        region: Earth Engine geometry
        threshold: Minimum % canopy cover to classify as forest
        hansen: Hansen GFW dataset image
        settings: Application settings

    Returns:
        Forest area in km²

    Raises:
        RuntimeError: If GEE computation fails after retries
    """
    treecover = hansen.select("treecover2000")
    forest_mask = treecover.gte(threshold)

    # Convert pixel count to km² (pixelArea() returns m²)
    area_img = forest_mask.multiply(ee.Image.pixelArea()).divide(1e6)  # type: ignore[attr-defined]

    return _reduce_region_with_retry(area_img, region, "treecover2000", settings)


def _calculate_loss_for_year(
    region: "Geometry", year: int, hansen: "Image", settings: Settings
) -> float:
    """Calculate forest loss area for a specific year in km².

    Args:
        region: Earth Engine geometry
        year: Year to calculate loss for (2001-2024)
        hansen: Hansen GFW dataset image
        settings: Application settings

    Returns:
        Loss area in km²

    Raises:
        RuntimeError: If GEE computation fails after retries
        ValueError: If year is outside valid range
    """
    lossyear = hansen.select("lossyear")

    # Hansen encoding: 1=2001, 2=2002, ..., 24=2024
    year_code = year - 2000
    if not 1 <= year_code <= 24:
        raise ValueError(f"Year {year} out of Hansen dataset range (2001-2024)")

    loss_mask = lossyear.eq(year_code)

    # Convert pixel count to km²
    area_img = loss_mask.multiply(ee.Image.pixelArea()).divide(1e6)  # type: ignore[attr-defined]

    return _reduce_region_with_retry(area_img, region, "lossyear", settings)


def _reduce_region_with_retry(
    image: "Image", geometry: "Geometry", band_name: str, settings: Settings
) -> float:
    """Execute GEE reduceRegion with exponential backoff retry logic.

    Args:
        image: Earth Engine image to reduce
        geometry: Region to reduce over
        band_name: Name of the band being reduced (for error messages)
        settings: Application settings with retry configuration

    Returns:
        Reduced value (sum of pixels)

    Raises:
        RuntimeError: If all retries fail
    """
    for attempt in range(settings.gee_max_retries):
        try:
            stats = image.reduceRegion(
                reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
                geometry=geometry,
                scale=settings.gee_scale_meters,
                maxPixels=settings.gee_max_pixels,
            )

            result = stats.getInfo()
            if result is None:
                return 0.0
            return float(result.get(band_name, 0.0))

        except ee.EEException as e:  # type: ignore[attr-defined]
            if attempt < settings.gee_max_retries - 1:
                wait_time = settings.gee_backoff_factor**attempt
                logger.warning(
                    f"GEE request failed (attempt {attempt + 1}/"
                    f"{settings.gee_max_retries}): {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"GEE request failed after {settings.gee_max_retries} attempts")
                raise RuntimeError(
                    f"Failed to compute {band_name} after {settings.gee_max_retries} retries"
                ) from e

    # Should never reach here, but satisfy type checker
    raise RuntimeError("Unexpected retry loop exit")
