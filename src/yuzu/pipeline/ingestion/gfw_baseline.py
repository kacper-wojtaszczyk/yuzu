"""Hansen Global Forest Watch baseline data extraction via Google Earth Engine.

This module handles extraction of annual forest loss data from the Hansen/UMD
Global Forest Change dataset (v1.12, 2000-2024) using Google Earth Engine's Python API.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import ee
import pandas as pd

from yuzu.config import get_settings

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
            raise ValueError(f"Tree cover threshold must be 0-100%, got {self.tree_cover_threshold}")


class GFWBaselineExtractor:
    """Extract Hansen GFW annual forest loss data via Google Earth Engine.

    This class handles:
    - GEE authentication and initialization
    - Extraction of year 2000 baseline tree cover
    - Annual forest loss calculation for specified year ranges
    - Retry logic for GEE API failures
    - Conversion of pixel counts to km²

    Example:
        >>> extractor = GFWBaselineExtractor(project_id="your-gee-project")
        >>> params = RegionExtraction(
        ...     region_id="test-region",
        ...     region_name="Test Protected Area",
        ...     geometry=geojson_dict,
        ...     start_year=2023,
        ...     end_year=2024
        ... )
        >>> df = extractor.extract_region(params)
    """

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize Google Earth Engine connection.

        Args:
            project_id: GEE project ID. If None, loads from settings.

        Raises:
            RuntimeError: If GEE initialization fails
        """
        settings = get_settings()
        self.project_id = project_id or settings.gee_project_id

        if not self.project_id:
            raise ValueError("GEE project ID must be provided or set in GEE_PROJECT_ID env var")

        self._initialize_ee()
        self.hansen = ee.Image(settings.hansen_asset_id)
        self.settings = settings
        logger.info(f"GFW extractor initialized with project: {self.project_id}")

    def _initialize_ee(self) -> None:
        """Initialize Earth Engine with retry logic."""
        try:
            ee.Initialize(project=self.project_id)
            logger.debug("Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {e}")
            raise RuntimeError(
                f"Earth Engine initialization failed. Ensure you've run 'earthengine authenticate' "
                f"and have access to project '{self.project_id}'"
            ) from e

    def extract_region(self, params: RegionExtraction) -> pd.DataFrame:
        """Extract annual forest loss data for a region.

        This method:
        1. Calculates year 2000 baseline forest area once
        2. Iterates through specified years, calculating loss per year
        3. Returns a DataFrame with annual loss metrics

        Args:
            params: Region extraction parameters

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
        """
        logger.info(
            f"Extracting GFW baseline for {params.region_name} "
            f"({params.start_year}-{params.end_year})"
        )

        region = ee.Geometry(params.geometry)

        # Calculate year 2000 baseline once
        baseline_km2 = self._calculate_baseline(region, params.tree_cover_threshold)
        logger.info(
            f"Year 2000 baseline: {baseline_km2:.2f} km² "
            f"(threshold: {params.tree_cover_threshold}%)"
        )

        # Extract loss by year
        results = []
        for year in range(params.start_year, params.end_year + 1):
            loss_km2 = self._calculate_loss_for_year(region, year)
            logger.debug(f"Year {year}: {loss_km2:.3f} km² loss")

            results.append({
                "region_id": params.region_id,
                "region_name": params.region_name,
                "year": year,
                "loss_km2": loss_km2,
                "baseline_cover_km2": baseline_km2,
                "tree_cover_threshold": params.tree_cover_threshold,
                "dataset_version": self.settings.hansen_dataset_version,
            })

        df = pd.DataFrame(results)
        logger.info(
            f"Extracted {len(df)} years. Total loss: {df['loss_km2'].sum():.2f} km² "
            f"({df['loss_km2'].sum() / baseline_km2 * 100:.2f}% of baseline)"
        )
        return df

    def _calculate_baseline(self, region: ee.Geometry, threshold: int) -> float:
        """Calculate year 2000 forest area in km².

        Args:
            region: Earth Engine geometry
            threshold: Minimum % canopy cover to classify as forest

        Returns:
            Forest area in km²

        Raises:
            RuntimeError: If GEE computation fails after retries
        """
        treecover = self.hansen.select("treecover2000")
        forest_mask = treecover.gte(threshold)

        # Convert pixel count to km² (pixelArea() returns m²)
        area_img = forest_mask.multiply(ee.Image.pixelArea()).divide(1e6)

        return self._reduce_region_with_retry(area_img, region, "treecover2000")

    def _calculate_loss_for_year(self, region: ee.Geometry, year: int) -> float:
        """Calculate forest loss area for a specific year in km².

        Args:
            region: Earth Engine geometry
            year: Year to calculate loss for (2001-2024)

        Returns:
            Loss area in km²

        Raises:
            RuntimeError: If GEE computation fails after retries
        """
        lossyear = self.hansen.select("lossyear")

        # Hansen encoding: 1=2001, 2=2002, ..., 24=2024
        year_code = year - 2000
        if not 1 <= year_code <= 24:
            raise ValueError(f"Year {year} out of Hansen dataset range (2001-2024)")

        loss_mask = lossyear.eq(year_code)

        # Convert pixel count to km²
        area_img = loss_mask.multiply(ee.Image.pixelArea()).divide(1e6)

        return self._reduce_region_with_retry(area_img, region, "lossyear")

    def _reduce_region_with_retry(
        self, image: ee.Image, geometry: ee.Geometry, band_name: str
    ) -> float:
        """Execute GEE reduceRegion with exponential backoff retry logic.

        Args:
            image: Earth Engine image to reduce
            geometry: Region to reduce over
            band_name: Name of the band being reduced (for error messages)

        Returns:
            Reduced value (sum of pixels)

        Raises:
            RuntimeError: If all retries fail
        """
        for attempt in range(self.settings.gee_max_retries):
            try:
                stats = image.reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=geometry,
                    scale=self.settings.gee_scale_meters,
                    maxPixels=self.settings.gee_max_pixels,
                )

                result = stats.getInfo()
                return float(result.get(band_name, 0.0))

            except ee.EEException as e:
                if attempt < self.settings.gee_max_retries - 1:
                    wait_time = self.settings.gee_backoff_factor**attempt
                    logger.warning(
                        f"GEE request failed (attempt {attempt + 1}/"
                        f"{self.settings.gee_max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"GEE request failed after {self.settings.gee_max_retries} attempts")
                    raise RuntimeError(
                        f"Failed to compute {band_name} after {self.settings.gee_max_retries} retries"
                    ) from e

        # Should never reach here, but satisfy type checker
        raise RuntimeError("Unexpected retry loop exit")

