from __future__ import annotations

import logging
import time
from pathlib import Path

import aiohttp

log = logging.getLogger(__name__)

_CHUNK_SIZE    = 1024 * 1024   # 1 MB
_LOG_INTERVAL  = 60            # seconds between progress messages


async def stream_csv(
    session: aiohttp.ClientSession,
    *,
    base_url: str,
    dataset_id: str,
    name: str,
    select_columns: str,
    app_token: str,
    csv_dir: Path,
) -> Path:
    """
    Streams a 3-column CSV from Socrata to {csv_dir}/tnp_{name}.csv.

    All dataset downloads are launched together via asyncio.gather()
    in download_orchestrator — this function handles exactly one dataset.

    Args:
        session:        shared aiohttp session (caller manages lifecycle)
        base_url:       Socrata resource base URL from config
        dataset_id:     4x4 Socrata dataset identifier
        name:           human label, used in filename and log messages
        select_columns: $select value (comma-separated column names)
        app_token:      Socrata app token ($$app_token param)
        csv_dir:        directory where CSV files are saved

    Returns:
        Path to the saved CSV file

    Raises:
        aiohttp.ClientResponseError: on non-2xx from Socrata
    """
    csv_dir.mkdir(exist_ok=True)
    out_path = csv_dir / f"tnp_{name}.csv"

    if out_path.exists():
        log.info("[%s] Already on disk — skipping download.", name)
        return out_path

    url    = f"{base_url}/{dataset_id}.csv"
    params = {
        "$select":     select_columns,
        "$limit":      9_999_999_999,   # effectively unlimited
        "$$app_token": app_token,
    }

    log.info("[%s] Streaming → %s ...", name, out_path)
    bytes_written = 0
    last_log      = time.monotonic()

    async with session.get(url, params=params) as response:
        response.raise_for_status()
        with open(out_path, "wb") as f:
            async for chunk in response.content.iter_chunked(_CHUNK_SIZE):
                f.write(chunk)
                bytes_written += len(chunk)

                now = time.monotonic()
                if now - last_log >= _LOG_INTERVAL:
                    log.info("[%s] %d MB downloaded ...", name, bytes_written // 1024 ** 2)
                    last_log = now

    log.info("[%s] %.1f MB saved", name, bytes_written / 1024 ** 2)
    return out_path
