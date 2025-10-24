"""Tests for Hansen baseline data extraction."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from yuzu.pipeline.ingestion.hansen_baseline import (
    RegionExtraction,
    extract_region,
    _calculate_baseline,
    _calculate_loss_for_year,
    _reduce_region_with_retry,
)


class TestRegionExtraction:
    """Tests for RegionExtraction dataclass."""

    def test_valid_parameters(self):
        """Test creation with valid parameters."""
        params = RegionExtraction(
            region_id="test-id",
            region_name="Test Region",
            geometry={"type": "Polygon", "coordinates": [[]]},
            start_year=2020,
            end_year=2024,
            tree_cover_threshold=30
        )

        assert params.region_id == "test-id"
        assert params.region_name == "Test Region"
        assert params.start_year == 2020
        assert params.end_year == 2024
        assert params.tree_cover_threshold == 30

    @patch('yuzu.pipeline.ingestion.hansen_baseline.get_settings')
    def test_default_tree_cover_threshold(self, mock_get_settings):
        """Test that tree cover threshold defaults from settings."""
        mock_settings = Mock()
        mock_settings.tree_cover_threshold = 40
        mock_get_settings.return_value = mock_settings

        params = RegionExtraction(
            region_id="test-id",
            region_name="Test Region",
            geometry={"type": "Polygon", "coordinates": [[]]},
            start_year=2020,
            end_year=2024
        )

        assert params.tree_cover_threshold == 40

    def test_invalid_year_range(self):
        """Test validation of year range."""
        with pytest.raises(ValueError, match="Invalid year range"):
            RegionExtraction(
                region_id="test-id",
                region_name="Test Region",
                geometry={"type": "Polygon", "coordinates": [[]]},
                start_year=2024,
                end_year=2020,  # End before start
                tree_cover_threshold=30
            )

    def test_invalid_threshold(self):
        """Test validation of tree cover threshold."""
        with pytest.raises(ValueError, match="Tree cover threshold must be 0-100%"):
            RegionExtraction(
                region_id="test-id",
                region_name="Test Region",
                geometry={"type": "Polygon", "coordinates": [[]]},
                start_year=2020,
                end_year=2024,
                tree_cover_threshold=150  # Invalid: > 100
            )


class TestExtractRegion:
    """Tests for extract_region function."""

    @patch('yuzu.pipeline.ingestion.hansen_baseline._calculate_loss_for_year')
    @patch('yuzu.pipeline.ingestion.hansen_baseline._calculate_baseline')
    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Geometry')
    def test_successful_extraction(self, mock_geometry, mock_calc_baseline, mock_calc_loss):
        """Test successful data extraction."""
        # Setup mocks
        mock_ee_context = Mock()
        mock_ee_context.hansen = Mock()
        mock_settings = Mock()
        mock_settings.hansen_dataset_version = "v1.12"
        mock_ee_context.settings = mock_settings

        mock_calc_baseline.return_value = 100.0
        mock_calc_loss.side_effect = [1.5, 2.3]  # Loss for 2023, 2024

        params = RegionExtraction(
            region_id="test-region-id",
            region_name="Test Region",
            geometry={"type": "Polygon", "coordinates": [[]]},
            start_year=2023,
            end_year=2024,
            tree_cover_threshold=30
        )

        # Execute
        result = extract_region(params, mock_ee_context)

        # Verify
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == [
            'region_id', 'region_name', 'year', 'loss_km2',
            'baseline_cover_km2', 'tree_cover_threshold', 'dataset_version'
        ]

        # Check first row (2023)
        assert result.iloc[0]['region_id'] == 'test-region-id'
        assert result.iloc[0]['region_name'] == 'Test Region'
        assert result.iloc[0]['year'] == 2023
        assert result.iloc[0]['loss_km2'] == 1.5
        assert result.iloc[0]['baseline_cover_km2'] == 100.0
        assert result.iloc[0]['tree_cover_threshold'] == 30
        assert result.iloc[0]['dataset_version'] == 'v1.12'

        # Check second row (2024)
        assert result.iloc[1]['year'] == 2024
        assert result.iloc[1]['loss_km2'] == 2.3


class TestCalculateBaseline:
    """Tests for _calculate_baseline function."""

    @patch('yuzu.pipeline.ingestion.hansen_baseline._reduce_region_with_retry')
    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Image')
    def test_baseline_calculation(self, mock_image, mock_reduce):
        """Test baseline calculation with proper GEE operations."""
        mock_reduce.return_value = 150.5

        mock_region = Mock()
        mock_hansen = Mock()
        mock_treecover = Mock()
        mock_hansen.select.return_value = mock_treecover
        mock_settings = Mock()

        result = _calculate_baseline(mock_region, 30, mock_hansen, mock_settings)

        assert result == 150.5
        mock_hansen.select.assert_called_once_with("treecover2000")
        mock_treecover.gte.assert_called_once_with(30)


class TestCalculateLossForYear:
    """Tests for _calculate_loss_for_year function."""

    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Image')
    @patch('yuzu.pipeline.ingestion.hansen_baseline._reduce_region_with_retry')
    def test_valid_year_calculation(self, mock_reduce, mock_ee_image):
        """Test loss calculation for valid year."""
        mock_reduce.return_value = 5.5

        # Mock the pixel area calculation
        mock_pixel_area = Mock()
        mock_ee_image.pixelArea.return_value = mock_pixel_area

        mock_region = Mock()
        mock_hansen = Mock()
        mock_lossyear = Mock()
        mock_hansen.select.return_value = mock_lossyear
        mock_settings = Mock()

        result = _calculate_loss_for_year(mock_region, 2023, mock_hansen, mock_settings)

        assert result == 5.5
        mock_hansen.select.assert_called_once_with("lossyear")
        mock_lossyear.eq.assert_called_once_with(23)  # 2023 - 2000 = 23

    def test_invalid_year_range(self):
        """Test that invalid years are rejected."""
        mock_region = Mock()
        mock_hansen = Mock()
        mock_settings = Mock()

        with pytest.raises(ValueError, match="out of Hansen dataset range"):
            _calculate_loss_for_year(mock_region, 2025, mock_hansen, mock_settings)

        with pytest.raises(ValueError, match="out of Hansen dataset range"):
            _calculate_loss_for_year(mock_region, 1999, mock_hansen, mock_settings)


class TestReduceRegionWithRetry:
    """Tests for _reduce_region_with_retry function."""

    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Reducer')
    def test_successful_first_attempt(self, mock_reducer):
        """Test successful computation on first try."""
        mock_reducer.sum.return_value = Mock()

        mock_image = Mock()
        mock_geometry = Mock()
        mock_stats = Mock()
        mock_stats.getInfo.return_value = {"test_band": 42.5}
        mock_image.reduceRegion.return_value = mock_stats

        mock_settings = Mock()
        mock_settings.gee_max_retries = 3
        mock_settings.gee_scale_meters = 30
        mock_settings.gee_max_pixels = 1e9
        mock_settings.gee_backoff_factor = 2.0

        result = _reduce_region_with_retry(mock_image, mock_geometry, "test_band", mock_settings)

        assert result == 42.5
        assert mock_image.reduceRegion.call_count == 1

    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Reducer')
    @patch('yuzu.pipeline.ingestion.hansen_baseline.time.sleep')
    def test_retry_on_failure(self, mock_sleep, mock_reducer):
        """Test retry logic on GEE failures."""
        from ee import EEException

        mock_reducer.sum.return_value = Mock()

        mock_image = Mock()
        mock_geometry = Mock()

        # Fail twice, then succeed
        mock_stats_success = Mock()
        mock_stats_success.getInfo.return_value = {"test_band": 42.5}
        mock_image.reduceRegion.side_effect = [
            EEException("Timeout"),
            EEException("Timeout"),
            mock_stats_success
        ]

        mock_settings = Mock()
        mock_settings.gee_max_retries = 3
        mock_settings.gee_scale_meters = 30
        mock_settings.gee_max_pixels = 1e9
        mock_settings.gee_backoff_factor = 2.0

        result = _reduce_region_with_retry(mock_image, mock_geometry, "test_band", mock_settings)

        assert result == 42.5
        assert mock_image.reduceRegion.call_count == 3
        assert mock_sleep.call_count == 2  # Slept after first two failures

    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Reducer')
    @patch('yuzu.pipeline.ingestion.hansen_baseline.time.sleep')
    def test_all_retries_exhausted(self, mock_sleep, mock_reducer):
        """Test that RuntimeError is raised after all retries fail."""
        from ee import EEException

        mock_reducer.sum.return_value = Mock()

        mock_image = Mock()
        mock_geometry = Mock()
        mock_image.reduceRegion.side_effect = EEException("Persistent failure")

        mock_settings = Mock()
        mock_settings.gee_max_retries = 3
        mock_settings.gee_scale_meters = 30
        mock_settings.gee_max_pixels = 1e9
        mock_settings.gee_backoff_factor = 2.0

        with pytest.raises(RuntimeError, match="Failed to compute test_band after 3 retries"):
            _reduce_region_with_retry(mock_image, mock_geometry, "test_band", mock_settings)

        assert mock_image.reduceRegion.call_count == 3

    @patch('yuzu.pipeline.ingestion.hansen_baseline.ee.Reducer')
    def test_returns_zero_when_band_missing(self, mock_reducer):
        """Test that missing band returns 0.0."""
        mock_reducer.sum.return_value = Mock()

        mock_image = Mock()
        mock_geometry = Mock()
        mock_stats = Mock()
        mock_stats.getInfo.return_value = {"other_band": 100.0}  # Missing 'test_band'
        mock_image.reduceRegion.return_value = mock_stats

        mock_settings = Mock()
        mock_settings.gee_max_retries = 3
        mock_settings.gee_scale_meters = 30
        mock_settings.gee_max_pixels = 1e9
        mock_settings.gee_backoff_factor = 2.0

        result = _reduce_region_with_retry(mock_image, mock_geometry, "test_band", mock_settings)

        assert result == 0.0

