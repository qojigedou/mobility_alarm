from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from domain.config import domain_settings
from domain.etl.db_schema import apply_schema
from domain.etl.download_orchestrator import download_all
from domain.etl.transformer import transform_and_load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def run() -> None:
    """
    Public API — runs the full ETL pipeline using domain_settings.
    """
    cfg = domain_settings
    t0  = datetime.now()

    log.info("=" * 55)
    log.info("Chicago TNP Trips + Weather ETL  (async)")
    log.info("  DB      : %s", cfg.db_path)
    log.info("  CSV dir : %s", cfg.csv_dir)
    log.info("  Datasets: %s", list(cfg.datasets.keys()))
    log.info("  Weather : %s -> today", cfg.weather_start)
    log.info("=" * 55)

    conn = apply_schema(str(cfg.db_path))

    log.info("Launching concurrent downloads ...")
    weather, csv_paths = asyncio.run(download_all())

    n_rows = transform_and_load(csv_paths, conn, weather)
    conn.close()

    elapsed = datetime.now() - t0
    log.info("")
    log.info("Done in %s — %s rows written", elapsed, f"{n_rows:,}")
    log.info("  DB: %s", cfg.db_path)
    log.info("Sample query:")
    log.info("  SELECT * FROM trips_summary ORDER BY total_trips DESC LIMIT 20;")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
