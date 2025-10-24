"""Google Earth Engine initialization and context management.

This module provides centralized Earth Engine authentication and initialization
that can be shared across all GEE-based extractors (Hansen baseline, GLAD alerts,
RADD alerts, Sentinel-2, etc.).

The Earth Engine SDK uses module-level global state, which this module wraps
in a clean interface to make dependencies explicit and testing easier.
"""

import logging
from dataclasses import dataclass, field

import ee

from yuzu.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EarthEngineContext:
    """Initialized Earth Engine context with commonly-used datasets.

    This context is shared across all GEE-based extractors. Datasets are
    lazy-loaded on first access to avoid unnecessary API calls.

    Attributes:
        project_id: GEE project ID used for initialization
        settings: Application settings with GEE configuration

    Example:
        >>> ee_ctx = initialize_earth_engine()
        >>> hansen_img = ee_ctx.hansen
    """

    project_id: str
    settings: object = field(repr=False)

    # Dataset references (lazy-loaded)
    _hansen: ee.Image | None = field(default=None, init=False, repr=False)

    @property
    def hansen(self) -> ee.Image:
        """Hansen Global Forest Change dataset (lazy-loaded).

        Returns:
            Earth Engine Image reference to Hansen GFW v1.12
        """
        if self._hansen is None:
            logger.debug(f"Loading Hansen dataset: {self.settings.hansen_asset_id}")
            self._hansen = ee.Image(self.settings.hansen_asset_id)
        return self._hansen



def initialize_earth_engine(project_id: str | None = None) -> EarthEngineContext:
    """Initialize Earth Engine and return context for data extraction.

    This function handles the global Earth Engine initialization (required by
    the EE SDK) and returns a context object that can be passed to any
    GEE-based extractor function.

    WARNING: The Earth Engine SDK uses module-level global state. Only one
    GEE project can be active per Python process. If you need to work with
    multiple projects, use separate processes.

    Args:
        project_id: GEE project ID from console.cloud.google.com/earth-engine.
                   If None, loads from GEE_PROJECT_ID environment variable.

    Returns:
        EarthEngineContext with initialized datasets

    Raises:
        ValueError: If project_id not provided and not in settings
        RuntimeError: If Earth Engine initialization fails

    Example:
        >>> # Initialize once at application startup
        >>> ee_ctx = initialize_earth_engine()
        >>>
        >>> # Pass to any extractor
        >>> from yuzu.pipeline.ingestion.hansen_baseline import extract_region
        >>> hansen_df = extract_region(params, ee_ctx)

    Note:
        This function must be called before any GEE data extraction.
        Authentication must be completed first via: earthengine authenticate
    """
    settings = get_settings()
    pid = project_id or settings.gee_project_id

    if not pid:
        raise ValueError(
            "GEE project ID must be provided as argument or set in GEE_PROJECT_ID "
            "environment variable"
        )

    try:
        ee.Initialize(project=pid)
        logger.info(f"Earth Engine initialized successfully with project: {pid}")
    except ee.EEException as e:
        logger.error(f"Failed to initialize Earth Engine: {e}")
        raise RuntimeError(
            f"Earth Engine initialization failed. Ensure you have:\n"
            f"1. Run 'earthengine authenticate' to set up credentials\n"
            f"2. Access to project '{pid}' in Google Cloud Console\n"
            f"3. Earth Engine API enabled for the project"
        ) from e

    return EarthEngineContext(project_id=pid, settings=settings)

