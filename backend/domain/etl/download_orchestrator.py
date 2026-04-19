from __future__ import annotations

import asyncio
import logging
import ssl
from pathlib import Path

import aiohttp
import certifi

from domain.config import domain_settings
from domain.etl.downloader import stream_csv
from domain.etl.weather_client import fetch_weather_marks

log = logging.getLogger(__name__)


async def download_all() -> tuple[dict[str, int], list[Path]]:
    """
    Fires off all downloads concurrently:
      - 1 weather request  (Open-Meteo archive, ~2 s)
      - N CSV streams       (Socrata, one per dataset, large)

    Total wall-clock time = max(individual download times), not their sum.

    Returns:
        (weather_marks, csv_paths)
        weather_marks: {YYYY-MM-DD: weather_mark int}
        csv_paths:     list of Paths to saved CSV files, in DATASETS order
    """
    cfg           = domain_settings
    ssl_context   = ssl.create_default_context(cafile=certifi.where())
    connector     = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=cfg.http_timeout,
    ) as session:
        weather_task = fetch_weather_marks(
            session,
            archive_url=cfg.weather_archive_url,
            lat=cfg.chicago_lat,
            lon=cfg.chicago_lon,
            start=cfg.weather_start,
        )

        csv_tasks = [
            stream_csv(
                session,
                base_url=cfg.socrata_base_url,
                dataset_id=dataset_id,
                name=name,
                select_columns=cfg.socrata_select,
                app_token=cfg.socrata_app_token,
                csv_dir=cfg.csv_dir,
            )
            for name, dataset_id in cfg.datasets.items()
        ]

        results = await asyncio.gather(weather_task, *csv_tasks)

    weather   = results[0]        # dict[str, int]
    csv_paths = list(results[1:]) # [Path, ...]
    return weather, csv_paths
