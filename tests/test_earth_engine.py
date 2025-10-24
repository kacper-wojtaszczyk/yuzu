"""Tests for Earth Engine initialization and context management."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from yuzu.pipeline.ingestion.earth_engine import (
    EarthEngineContext,
    initialize_earth_engine,
)


class TestEarthEngineContext:
    """Tests for EarthEngineContext dataclass."""

    def test_context_initialization(self):
        """Test basic context creation."""
        mock_settings = Mock()
        mock_settings.hansen_asset_id = "UMD/hansen/test"

        context = EarthEngineContext(
            project_id="test-project",
            settings=mock_settings
        )

        assert context.project_id == "test-project"
        assert context.settings == mock_settings
        assert context._hansen is None

    @patch('yuzu.pipeline.ingestion.earth_engine.ee.Image')
    def test_hansen_lazy_loading(self, mock_image):
        """Test that Hansen dataset is loaded lazily."""
        mock_settings = Mock()
        mock_settings.hansen_asset_id = "UMD/hansen/test"
        mock_image_instance = Mock()
        mock_image.return_value = mock_image_instance

        context = EarthEngineContext(
            project_id="test-project",
            settings=mock_settings
        )

        # First access should load
        result = context.hansen
        mock_image.assert_called_once_with("UMD/hansen/test")
        assert result == mock_image_instance

        # Second access should use cached value
        result2 = context.hansen
        mock_image.assert_called_once()  # Not called again
        assert result2 == mock_image_instance


class TestInitializeEarthEngine:
    """Tests for initialize_earth_engine function."""

    @patch('yuzu.pipeline.ingestion.earth_engine.ee.Initialize')
    @patch('yuzu.pipeline.ingestion.earth_engine.get_settings')
    def test_successful_initialization(self, mock_get_settings, mock_ee_init):
        """Test successful Earth Engine initialization."""
        mock_settings = Mock()
        mock_settings.gee_project_id = "test-project"
        mock_get_settings.return_value = mock_settings

        context = initialize_earth_engine()

        mock_ee_init.assert_called_once_with(project="test-project")
        assert isinstance(context, EarthEngineContext)
        assert context.project_id == "test-project"
        assert context.settings == mock_settings

    @patch('yuzu.pipeline.ingestion.earth_engine.ee.Initialize')
    @patch('yuzu.pipeline.ingestion.earth_engine.get_settings')
    def test_initialization_with_explicit_project_id(self, mock_get_settings, mock_ee_init):
        """Test initialization with explicitly provided project ID."""
        mock_settings = Mock()
        mock_settings.gee_project_id = "default-project"
        mock_get_settings.return_value = mock_settings

        context = initialize_earth_engine(project_id="override-project")

        mock_ee_init.assert_called_once_with(project="override-project")
        assert context.project_id == "override-project"

    @patch('yuzu.pipeline.ingestion.earth_engine.get_settings')
    def test_initialization_without_project_id(self, mock_get_settings):
        """Test initialization fails when no project ID is available."""
        mock_settings = Mock()
        mock_settings.gee_project_id = ""
        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="GEE project ID must be provided"):
            initialize_earth_engine()

    @patch('yuzu.pipeline.ingestion.earth_engine.ee.Initialize')
    @patch('yuzu.pipeline.ingestion.earth_engine.get_settings')
    def test_initialization_failure(self, mock_get_settings, mock_ee_init):
        """Test initialization handles Earth Engine errors."""
        mock_settings = Mock()
        mock_settings.gee_project_id = "test-project"
        mock_get_settings.return_value = mock_settings

        from ee import EEException
        mock_ee_init.side_effect = EEException("Authentication failed")

        with pytest.raises(RuntimeError, match="Earth Engine initialization failed"):
            initialize_earth_engine()

