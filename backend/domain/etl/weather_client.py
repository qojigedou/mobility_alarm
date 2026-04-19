from __future__ import annotations

import logging
from datetime import date

import aiohttp

from tools.data_formatter import compute_weather_mark, month_to_season

log = logging.getLogger(__name__)


async def fetch_weather_marks(
    session: aiohttp.ClientSession,
    *,
    archive_url: str,
    lat: float,
    lon: float,
    start: str,
    end: str | None = None,
) -> dict[str, int]:
    """
    Fetches daily weather data from Open-Meteo and returns
    a {YYYY-MM-DD: weather_mark} dict for every day in [start, end].

    Designed to run concurrently inside asyncio.gather() alongside
    CSV downloads — it does not block the event loop.

    Args:
        session:     shared aiohttp session (caller manages lifecycle)
        archive_url: Open-Meteo archive endpoint from config
        lat:         city latitude
        lon:         city longitude
        start:       ISO date string e.g. "2018-11-01"
        end:         ISO date string; defaults to today

    Raises:
        aiohttp.ClientResponseError: on non-2xx from Open-Meteo
    """
    if end is None:
        end = date.today().isoformat()

    log.info("[weather] Fetching %s → %s ...", start, end)

    params = {
        "latitude":         lat,
        "longitude":        lon,
        "start_date":       start,
        "end_date":         end,
        "daily":            "temperature_2m_max,precipitation_sum,snowfall_sum",
        "temperature_unit": "celsius",
        "timezone":         "America/Chicago",
    }

    async with session.get(archive_url, params=params) as response:
        response.raise_for_status()
        payload = await response.json(content_type=None)

    daily = payload["daily"]
    marks: dict[str, int] = {}

    for dt, temp, precip, snowfall in zip(
        daily["time"],
        daily["temperature_2m_max"],
        daily["precipitation_sum"],
        daily["snowfall_sum"],
    ):
        season    = month_to_season(int(dt[5:7]))
        marks[dt] = int(compute_weather_mark(
            float(snowfall or 0),
            float(precip   or 0),
            float(temp     or 0),
            season,
        ))

    log.info("[weather] %d days loaded", len(marks))
    return marks
