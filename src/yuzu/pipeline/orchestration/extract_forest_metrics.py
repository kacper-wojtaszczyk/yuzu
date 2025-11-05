"""Extract forest change metrics using Google Earth Engine Dynamic World dataset.

This script calculates forest cover loss between a baseline period (monthly aggregate)
and a recent period (weekly aggregate) for a specified region in the Amazon.

The metrics are designed to be used as inputs for LLM-based narrative generation.
"""

import sys
from datetime import datetime, timedelta
from typing import Any

import ee

from yuzu.config import get_settings

# ===== Configuration =====

# Forest classification threshold
# Pixels with tree probability > FOREST_THRESHOLD are considered forest
FOREST_THRESHOLD = 0.15

# Region of Interest: Amazon (Pará/Amazonas border)
# GeoJSON polygon defining the area to analyze
REGION_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    [
                        [
                            -52.04455810982353,
                            -6.547275444534847
                        ],
                        [
                            -52.21975739509983,
                            -6.691384453774532
                        ],
                        [
                            -52.13806784324625,
                            -6.945484904466241
                        ],
                        [
                            -51.66467929443996,
                            -6.960805278853911
                        ],
                        [
                            -51.526139370991245,
                            -6.606258488949791
                        ],
                        [
                            -51.94843113604719,
                            -6.441381005958675
                        ],
                        [
                            -52.04455810982353,
                            -6.547275444534847
                        ]
                    ]
                ],
                "type": "Polygon",
            },
        }
    ],
}

# Time periods for analysis
# Script will generate monthly composites for each month in this range
ANALYSIS_START = "2025-05-01"
ANALYSIS_END = "2025-10-30"  # End date (exclusive)

# Aggregation window in days (default: ~30 days for monthly)
AGGREGATION_WINDOW_DAYS = 30

# Gap-filling configuration
ENABLE_GAP_FILLING = True  # Fill missing pixels with historical data
MAX_LOOKBACK_DAYS = 180  # Maximum days to look back for historical data

# Dynamic World collection ID
DYNAMIC_WORLD_COLLECTION = "GOOGLE/DYNAMICWORLD/V1"


# ===== Helper Functions =====


def initialize_earth_engine() -> None:
    """Initialize Google Earth Engine with project credentials.

    Uses credentials from environment configuration. Falls back to
    interactive authentication if service account is not configured.
    """
    settings = get_settings()

    try:
        ee.Initialize(project=settings.gee_project_id)
        print("✓ Earth Engine initialized with interactive authentication")
    except Exception as e:
        print(f"✗ Failed to initialize Earth Engine: {e}", file=sys.stderr)
        print("\nPlease authenticate by running: earthengine authenticate", file=sys.stderr)
        sys.exit(1)


def get_region_geometry() -> Any:
    """Load region of interest from GeoJSON configuration.

    Returns:
        ee.Geometry: Earth Engine geometry object for the region.
    """
    # Extract coordinates from GeoJSON
    coords = REGION_GEOJSON["features"][0]["geometry"]["coordinates"][0]  # type: ignore[index]
    return ee.Geometry.Polygon(coords)  # type: ignore[attr-defined]


def calculate_forest_area(
        region: Any,
        start_date: str,
        end_date: str,
        threshold: float = FOREST_THRESHOLD,
        enable_gap_filling: bool = True,
        max_lookback_days: int = 180,
        total_region_m2: float = 0,
) -> tuple[float, int, float, float]:
    """Calculate forest area for a given time period with adaptive gap-filling.

    Args:
        region: Earth Engine geometry defining the area of interest (ee.Geometry)
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        threshold: Tree probability threshold for forest classification
        enable_gap_filling: If True, fills missing pixels with historical data
        max_lookback_days: Maximum days to look back for gap-filling

    Returns:
        Tuple of (forest area in hectares, number of valid images used,
                  area with current data in hectares, total area covered after gap-filling in hectares)
    """
    # Query Dynamic World collection for current period
    dw_current = (
        ee.ImageCollection(DYNAMIC_WORLD_COLLECTION)  # type: ignore[attr-defined]
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .select(["label", "trees"])
    )

    # Get image count for current period
    image_count = dw_current.size().getInfo()

    pixel_area = ee.Image.pixelArea()  # type: ignore[attr-defined]  # m²

    # Calculate composites for current period
    if image_count > 0:
        current_label = dw_current.select("label").mode()
        current_trees = dw_current.select("trees").mean()
    else:
        # No data in current period - create empty images
        current_label = ee.Image.constant(0).select([0], ["label"]).updateMask(0)  # type: ignore[attr-defined]
        current_trees = ee.Image.constant(0).select([0], ["trees"]).updateMask(0)  # type: ignore[attr-defined]

    # Calculate current period coverage
    current_coverage_mask = current_label.mask()
    current_covered_m2 = current_coverage_mask.multiply(pixel_area)
    current_stats = current_covered_m2.reduceRegion(
        reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
        geometry=region,
        scale=10,
        maxPixels=1e10,
    )
    current_covered_m2_value = current_stats.get("label").getInfo()
    current_covered_ha = current_covered_m2_value / 10000 if current_covered_m2_value else 0

    # Gap-filling: adaptively fill missing pixels using most recent historical data
    # aggregated over the same window period
    final_label = current_label
    final_trees = current_trees

    if enable_gap_filling:
        # Search backwards in AGGREGATION_WINDOW_DAYS chunks to find historical periods
        # We'll try multiple historical windows going back up to max_lookback_days
        lookback_start = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(
            days=max_lookback_days
        )

        # Collect historical composites for each window going backwards
        historical_composites = []
        current_window_end = datetime.strptime(start_date, "%Y-%m-%d")

        # Generate historical windows going backwards
        num_windows = max_lookback_days // AGGREGATION_WINDOW_DAYS
        for _ in range(num_windows):
            window_start = current_window_end - timedelta(days=AGGREGATION_WINDOW_DAYS)

            # Get data for this historical window
            dw_window = (
                ee.ImageCollection(DYNAMIC_WORLD_COLLECTION)  # type: ignore[attr-defined]
                .filterBounds(region)
                .filterDate(
                    window_start.strftime("%Y-%m-%d"), current_window_end.strftime("%Y-%m-%d")
                )
                .select(["label", "trees"])
            )

            if dw_window.size().getInfo() > 0:
                # Aggregate over the window (same as current period)
                window_label = dw_window.select("label").mode()
                window_trees = dw_window.select("trees").mean()

                # Add timestamp for ordering (use window end date as timestamp)
                timestamp_val = int(current_window_end.timestamp() * 1000)
                window_composite = window_label.addBands(window_trees).addBands(
                    ee.Image.constant(timestamp_val).toInt64().rename("timestamp")  # type: ignore[attr-defined]
                )
                historical_composites.append(window_composite)

            current_window_end = window_start

        if historical_composites:
            # Create collection from historical composites and use qualityMosaic
            # to select most recent (highest timestamp) valid pixel for each location
            historical_collection = ee.ImageCollection(historical_composites)  # type: ignore[attr-defined]
            most_recent_mosaic = historical_collection.qualityMosaic("timestamp")

            historical_label = most_recent_mosaic.select("label")
            historical_trees = most_recent_mosaic.select("trees")

            # Fill gaps: use current where available, historical otherwise
            final_label = current_label.unmask(historical_label)
            final_trees = current_trees.unmask(historical_trees)

        # Check if we achieved 100% coverage
        final_coverage_check = final_label.mask()
        check_stats = final_coverage_check.multiply(pixel_area).reduceRegion(
            reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
            geometry=region,
            scale=10,
            maxPixels=1e10,
        )
        check_coverage = check_stats.get("label").getInfo()
        check_coverage_ha = check_coverage / 10000 if check_coverage else 0
        check_pct = (check_coverage_ha / (total_region_m2 / 10000) * 100) if total_region_m2 else 0

        # If we still don't have 100% coverage, extend lookback further
        if check_pct < 99.9 and historical_composites:
            # Go back even further (up to 1 year total) to ensure full coverage
            extended_window_end = lookback_start
            extended_lookback = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)

            extended_composites = []
            while extended_window_end > extended_lookback:
                window_start = extended_window_end - timedelta(days=AGGREGATION_WINDOW_DAYS)

                dw_window = (
                    ee.ImageCollection(DYNAMIC_WORLD_COLLECTION)  # type: ignore[attr-defined]
                    .filterBounds(region)
                    .filterDate(
                        window_start.strftime("%Y-%m-%d"), extended_window_end.strftime("%Y-%m-%d")
                    )
                    .select(["label", "trees"])
                )

                if dw_window.size().getInfo() > 0:
                    window_label = dw_window.select("label").mode()
                    window_trees = dw_window.select("trees").mean()

                    timestamp_val = int(extended_window_end.timestamp() * 1000)
                    window_composite = window_label.addBands(window_trees).addBands(
                        ee.Image.constant(timestamp_val).toInt64().rename("timestamp")  # type: ignore[attr-defined]
                    )
                    extended_composites.append(window_composite)

                extended_window_end = window_start

            if extended_composites:
                extended_collection = ee.ImageCollection(extended_composites)  # type: ignore[attr-defined]
                extended_mosaic = extended_collection.qualityMosaic("timestamp")
                extended_label = extended_mosaic.select("label")
                extended_trees = extended_mosaic.select("trees")

                # Fill any remaining gaps with extended historical data
                final_label = final_label.unmask(extended_label)
                final_trees = final_trees.unmask(extended_trees)

    # Calculate total coverage after gap-filling
    final_coverage_mask = final_label.mask()
    final_covered_m2 = final_coverage_mask.multiply(pixel_area)
    final_stats = final_covered_m2.reduceRegion(
        reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
        geometry=region,
        scale=10,
        maxPixels=1e10,
    )
    final_covered_m2_value = final_stats.get("label").getInfo()
    final_covered_ha = final_covered_m2_value / 10000 if final_covered_m2_value else 0

    # Create forest mask using gap-filled data
    is_forest_class = final_label.eq(1)  # 1 = trees class in Dynamic World
    is_confident = final_trees.gte(threshold)
    forest_mask = is_forest_class.And(is_confident)

    # Calculate forest area
    forest_area_m2 = forest_mask.multiply(pixel_area)

    # Sum forest area within region and convert to hectares
    stats = forest_area_m2.reduceRegion(
        reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
        geometry=region,
        scale=10,
        maxPixels=1e10,
    )

    area_m2 = stats.get("label").getInfo()
    area_ha = area_m2 / 10000 if area_m2 else 0

    return area_ha, image_count, current_covered_ha, final_covered_ha


def generate_time_periods(
        start_date: str,
        end_date: str,
        window_days: int,
) -> list[tuple[str, str]]:
    """Generate time periods for analysis.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (exclusive)
        window_days: Number of days in each aggregation window

    Returns:
        List of (start, end) date tuples in 'YYYY-MM-DD' format
    """
    periods = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current < end:
        period_end = current + timedelta(days=window_days)
        if period_end > end:
            period_end = end

        periods.append(
            (
                current.strftime("%Y-%m-%d"),
                period_end.strftime("%Y-%m-%d"),
            )
        )
        current = period_end

    return periods


def format_time_series_output(
        time_series: list[tuple[str, str, float, int, float, float]],
        total_region_area: float,
) -> str:
    """Format time series metrics for console output.

    Args:
        time_series: List of (start_date, end_date, area_ha, image_count, current_covered_ha, final_covered_ha) tuples
        total_region_area: Total area of the region in hectares

    Returns:
        Formatted string with time series metrics
    """
    output = f"""
{"=" * 80}
FOREST COVER TIME SERIES ANALYSIS
{"=" * 80}

Region: Amazon (São Felix do Xingu)
Threshold: {FOREST_THRESHOLD} (tree probability)
Aggregation Window: {AGGREGATION_WINDOW_DAYS} days
Analysis Period: {ANALYSIS_START} to {ANALYSIS_END}

{"=" * 80}
MONTHLY FOREST AREA MEASUREMENTS
{"=" * 80}

"""

    # Calculate period-over-period changes
    for i, (start, end, area, img_count, current_covered_ha, final_covered_ha) in enumerate(
            time_series
    ):
        period_label = f"Period {i + 1}"
        current_coverage_pct = (
            (current_covered_ha / total_region_area * 100) if total_region_area > 0 else 0
        )
        final_coverage_pct = (
            (final_covered_ha / total_region_area * 100) if total_region_area > 0 else 0
        )
        gap_filled_pct = final_coverage_pct - current_coverage_pct

        output += f"{period_label:12} ({start} to {end})\n"
        output += f"             Forest Area: {area:>12,.2f} ha\n"
        output += f"             Images Used: {img_count:>12} images"

        # Flag periods with insufficient data
        if img_count < 3:
            output += " ⚠️  LOW DATA"
        output += "\n"

        output += f"             Current Cov.:{current_covered_ha:>12,.2f} ha ({current_coverage_pct:>5.1f}%)"
        if ENABLE_GAP_FILLING and gap_filled_pct > 1:
            output += f"\n             Gap-Filled:  {final_covered_ha:>12,.2f} ha ({final_coverage_pct:>5.1f}%) [+{gap_filled_pct:.1f}% from history]"
        output += "\n"

        if i > 0:
            prev_area = time_series[i - 1][2]
            change_ha = area - prev_area
            change_pct = (change_ha / prev_area * 100) if prev_area > 0 else 0

            status = "📈 Growth" if change_ha > 0 else "📉 Loss" if change_ha < 0 else "➡️  Stable"
            output += f"             Change:      {change_ha:>+12,.2f} ha ({change_pct:>+6.2f}%) {status}\n"

        output += "\n"

    # Summary statistics
    if len(time_series) > 1:
        first_area = time_series[0][2]
        last_area = time_series[-1][2]
        total_change = last_area - first_area
        total_pct = (total_change / first_area * 100) if first_area > 0 else 0

        min_area = min(area for _, _, area, _, _, _ in time_series)
        max_area = max(area for _, _, area, _, _, _ in time_series)
        avg_area = sum(area for _, _, area, _, _, _ in time_series) / len(time_series)

        # Data quality metrics
        total_images = sum(img_count for _, _, _, img_count, _, _ in time_series)
        avg_images = total_images / len(time_series)
        low_data_periods = sum(1 for _, _, _, img_count, _, _ in time_series if img_count < 3)

        # Coverage metrics (using final gap-filled coverage)
        avg_current_coverage = sum(current_cov for _, _, _, _, current_cov, _ in time_series) / len(
            time_series
        )
        avg_final_coverage = sum(final_cov for _, _, _, _, _, final_cov in time_series) / len(
            time_series
        )
        avg_current_pct = (
            (avg_current_coverage / total_region_area * 100) if total_region_area > 0 else 0
        )
        avg_final_pct = (
            (avg_final_coverage / total_region_area * 100) if total_region_area > 0 else 0
        )
        avg_gap_filled = avg_final_pct - avg_current_pct

        partial_coverage_periods = sum(
            1
            for _, _, _, _, current_cov, _ in time_series
            if (current_cov / total_region_area * 100) < 80
        )

        output += f"""
{"=" * 80}
SUMMARY STATISTICS
{"=" * 80}

Total Change:        {total_change:>12,.2f} ha ({total_pct:>+6.2f}%)
Minimum Area:        {min_area:>12,.2f} ha
Maximum Area:        {max_area:>12,.2f} ha
Average Area:        {avg_area:>12,.2f} ha
Volatility:          {max_area - min_area:>12,.2f} ha ({((max_area - min_area) / avg_area * 100):>.1f}% of avg)

{"=" * 80}
DATA QUALITY ASSESSMENT
{"=" * 80}

Region Total Area:   {total_region_area:>12,.2f} ha

IMAGE AVAILABILITY:
Total Images:        {total_images:>12} images across all periods
Average per Period:  {avg_images:>12.1f} images
Low Data Periods:    {low_data_periods:>12} periods (< 3 images)

COVERAGE COMPLETENESS:
Current Period Avg:  {avg_current_coverage:>12,.2f} ha ({avg_current_pct:>5.1f}% of region)
After Gap-Filling:   {avg_final_coverage:>12,.2f} ha ({avg_final_pct:>5.1f}% of region)
Gap-Filled Avg:      {avg_gap_filled:>12.1f}% from historical data
Partial Coverage:    {partial_coverage_periods:>12} periods (< 80% current coverage)

{"⚠️  WARNING" if low_data_periods > 0 or partial_coverage_periods > 0 else "✓"}  {"Cloud coverage issues detected!" if low_data_periods > 0 or partial_coverage_periods > 0 else "Good data quality across all periods."}
{"   " if low_data_periods == 0 else f"   - {low_data_periods} periods with < 3 images (unreliable)"}
{"   " if partial_coverage_periods == 0 else f"   - {partial_coverage_periods} periods with < 80% current coverage"}
{"   " if not ENABLE_GAP_FILLING or avg_gap_filled < 1 else f"   - Gap-filling added {avg_gap_filled:.1f}% coverage on average"}

{"✓" if ENABLE_GAP_FILLING else "⚠️"}  Gap-filling: {"ENABLED" if ENABLE_GAP_FILLING else "DISABLED"} (lookback: {MAX_LOOKBACK_DAYS} days)
     {"Missing pixels filled with most recent historical observations (within lookback window)." if ENABLE_GAP_FILLING else "Results only account for pixels with data in current period."}
     {"Helps maintain consistent coverage across periods despite cloud interference." if ENABLE_GAP_FILLING else "May cause volatility due to changing coverage patterns."}

{"=" * 80}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{"=" * 80}
"""
    return output


# ===== Main Execution =====


def main() -> None:
    """Execute forest metrics extraction pipeline."""
    print("Starting forest metrics extraction...")
    print("-" * 80)

    # Initialize Earth Engine
    print("Step 1/3: Initializing Earth Engine...")
    initialize_earth_engine()

    # Load region
    print("Step 2/3: Loading region geometry...")
    region = get_region_geometry()
    print("✓ Region loaded successfully")

    # Generate time periods
    print("Step 3/3: Calculating forest area time series...")
    print(f"  Date range: {ANALYSIS_START} to {ANALYSIS_END}")
    print(f"  Aggregation window: {AGGREGATION_WINDOW_DAYS} days")

    periods = generate_time_periods(
        start_date=ANALYSIS_START,
        end_date=ANALYSIS_END,
        window_days=AGGREGATION_WINDOW_DAYS,
    )

    print(f"  Generated {len(periods)} time periods")
    print()

    # Calculate total region area for coverage comparison
    pixel_area = ee.Image.pixelArea()  # type: ignore[attr-defined]
    region_stats = pixel_area.reduceRegion(
        reducer=ee.Reducer.sum(),  # type: ignore[attr-defined]
        geometry=region,
        scale=10,
        maxPixels=1e10,
    )
    total_region_m2 = region_stats.get("area").getInfo()
    total_region_ha = total_region_m2 / 10000 if total_region_m2 else 0
    print(f"  Total region area: {total_region_ha:,.2f} ha")
    print()

    # Calculate forest area for each period
    time_series: list[tuple[str, str, float, int, float, float]] = []

    for i, (start, end) in enumerate(periods, 1):
        print(f"  [{i}/{len(periods)}] Processing {start} to {end}...", end=" ")

        area, img_count, current_covered_ha, final_covered_ha = calculate_forest_area(
            region=region,
            start_date=start,
            end_date=end,
            enable_gap_filling=ENABLE_GAP_FILLING,
            max_lookback_days=MAX_LOOKBACK_DAYS,
            total_region_m2=total_region_m2,
        )

        time_series.append((start, end, area, img_count, current_covered_ha, final_covered_ha))
        current_pct = (current_covered_ha / total_region_ha * 100) if total_region_ha > 0 else 0
        final_pct = (final_covered_ha / total_region_ha * 100) if total_region_ha > 0 else 0
        warning = " ⚠️  LOW DATA" if img_count < 3 else ""

        if ENABLE_GAP_FILLING and final_pct > current_pct + 1:
            coverage_str = f"{final_pct:.0f}% [+{final_pct - current_pct:.0f}% filled]"
        else:
            coverage_str = f"{current_pct:.0f}%"

        print(f"✓ {area:,.2f} ha ({img_count} imgs, {coverage_str}){warning}")

    # Format and display results
    print("\n" + format_time_series_output(time_series, total_region_ha))


if __name__ == "__main__":
    main()
