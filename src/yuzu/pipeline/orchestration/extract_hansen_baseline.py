"""CLI script for extracting Hansen GFW baseline data.

This script provides a command-line interface for manually extracting
historical forest loss data from Google Earth Engine. It will later be
converted into an orchestration task (e.g., Prefect flow).

Usage:
    python -m yuzu.pipeline.orchestration.extract_hansen_baseline \\
        --region-id <uuid> \\
        --start-year 2023 \\
        --end-year 2024

Requirements:
    - Earth Engine authentication: run 'earthengine authenticate' first
    - GEE_PROJECT_ID configured in .env
    - Region geometry loaded in forest.forest_regions table
"""

import argparse
import logging
import sys
from uuid import UUID

import pandas as pd
from sqlalchemy import create_engine, text

from yuzu.config import get_settings
from yuzu.pipeline.ingestion.earth_engine import initialize_earth_engine
from yuzu.pipeline.ingestion.hansen_baseline import RegionExtraction, extract_region

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_region_geometry(region_id: UUID) -> tuple[str, str, dict]:
    """Load region metadata and geometry from database.

    Args:
        region_id: UUID of the region to extract

    Returns:
        Tuple of (region_name, region_type, geometry_geojson)

    Raises:
        ValueError: If region not found
    """
    settings = get_settings()
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT region_name, region_type, ST_AsGeoJSON(geometry) as geometry
                FROM forest.forest_regions
                WHERE region_id = :region_id
            """),
            {"region_id": str(region_id)}
        ).fetchone()

        if not result:
            raise ValueError(f"Region {region_id} not found in forest.forest_regions table")

        import json
        return result.region_name, result.region_type, json.loads(result.geometry)


def store_results(df: pd.DataFrame) -> None:
    """Store extraction results in database.

    Uses manual INSERT to properly handle UUID type casting.

    Args:
        df: DataFrame with extraction results
    """
    settings = get_settings()
    engine = create_engine(settings.database_url)

    logger.info(f"Storing {len(df)} records in forest.forest_annual_loss table")

    with engine.connect() as conn:
        # Manual INSERT with proper UUID casting
        for _, row in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO forest.forest_annual_loss 
                    (region_id, year, loss_km2, baseline_cover_km2, 
                     tree_cover_threshold, dataset_version)
                    VALUES 
                    (CAST(:region_id AS uuid), :year, :loss_km2, :baseline_cover_km2,
                     :tree_cover_threshold, :dataset_version)
                """),
                {
                    "region_id": row["region_id"],
                    "year": int(row["year"]),
                    "loss_km2": float(row["loss_km2"]),
                    "baseline_cover_km2": float(row["baseline_cover_km2"]),
                    "tree_cover_threshold": int(row["tree_cover_threshold"]),
                    "dataset_version": row["dataset_version"],
                }
            )
        conn.commit()

    logger.info("✓ Data stored successfully")


def main() -> int:
    """Main entry point for the CLI script.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Extract Hansen GFW baseline data for a region",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 2 years for a region
  python -m yuzu.pipeline.orchestration.extract_hansen_baseline \\
      --region-id 12345678-1234-1234-1234-123456789abc \\
      --start-year 2023 \\
      --end-year 2024

  # Extract full historical range with custom threshold
  python -m yuzu.pipeline.orchestration.extract_hansen_baseline \\
      --region-id 12345678-1234-1234-1234-123456789abc \\
      --start-year 2000 \\
      --end-year 2024 \\
      --threshold 40

  # Dry run (extract but don't store)
  python -m yuzu.pipeline.orchestration.extract_hansen_baseline \\
      --region-id 12345678-1234-1234-1234-123456789abc \\
      --start-year 2023 \\
      --end-year 2024 \\
      --dry-run
        """
    )

    parser.add_argument(
        "--region-id",
        type=UUID,
        required=True,
        help="UUID of the region (from forest.forest_regions table)"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2023,
        help="First year to extract (inclusive, default: 2023)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2024,
        help="Last year to extract (inclusive, default: 2024)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Tree cover threshold %% (default: use config value, typically 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract data but don't store in database"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save results to CSV file (optional)"
    )

    args = parser.parse_args()

    try:
        # Step 1: Initialize Earth Engine
        logger.info("Initializing Google Earth Engine...")
        ee_context = initialize_earth_engine()
        logger.info(f"✓ Connected to GEE project: {ee_context.project_id}")

        # Step 2: Load region from database
        logger.info(f"Loading region {args.region_id} from database...")
        region_name, region_type, geometry = load_region_geometry(args.region_id)
        logger.info(f"✓ Found region: {region_name} ({region_type})")

        # Step 3: Create extraction parameters
        params = RegionExtraction(
            region_id=str(args.region_id),
            region_name=region_name,
            geometry=geometry,
            start_year=args.start_year,
            end_year=args.end_year,
            tree_cover_threshold=args.threshold
        )

        # Step 4: Extract data from GEE
        logger.info("Extracting Hansen GFW baseline data...")
        df = extract_region(params, ee_context)

        # Step 5: Display summary
        logger.info("\n" + "="*60)
        logger.info(f"Extraction Summary for {region_name}")
        logger.info("="*60)
        logger.info(f"Years extracted: {args.start_year}-{args.end_year}")
        logger.info(f"Baseline (2000): {df['baseline_cover_km2'].iloc[0]:.2f} km²")
        logger.info(f"Total loss: {df['loss_km2'].sum():.2f} km²")
        logger.info(f"Loss rate: {df['loss_km2'].sum() / df['baseline_cover_km2'].iloc[0] * 100:.2f}%")
        logger.info(f"Tree cover threshold: {df['tree_cover_threshold'].iloc[0]}%")
        logger.info(f"Dataset version: {df['dataset_version'].iloc[0]}")
        logger.info("="*60 + "\n")

        # Step 6: Save to CSV if requested
        if args.output:
            df.to_csv(args.output, index=False)
            logger.info(f"✓ Results saved to {args.output}")

        # Step 7: Store in database (unless dry run)
        if args.dry_run:
            logger.info("DRY RUN: Skipping database storage")
            logger.info(f"Would have inserted {len(df)} records")
        else:
            store_results(df)

        logger.info("\n✓ Extraction completed successfully")
        return 0

    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

