from __future__ import annotations
from datetime import date, datetime

import aiohttp
from fastapi import HTTPException

from app.config import settings
from app.tools.data_formatter import (
    WEATHER_LABEL,
    compute_weather_mark,
    month_to_season,
    hour_to_daytime,
)
from app.models.schemas import CurrentWeather


async def fetch_current_weather(http: aiohttp.ClientSession) -> CurrentWeather:
    today = date.today()
    now   = datetime.now()

    params = {
        "latitude":         settings.chicago_lat,
        "longitude":        settings.chicago_lon,
        "daily":            "temperature_2m_max,precipitation_sum,snowfall_sum",
        "temperature_unit": "celsius",
        "timezone":         "America/Chicago",
        "forecast_days":    1,
    }

    async with http.get(settings.open_meteo_url, params=params) as r:
        if r.status != 200:
            raise HTTPException(status_code=502, detail="Weather API unavailable")
        data = await r.json(content_type=None)

    daily    = data["daily"]
    temp     = float(daily["temperature_2m_max"][0] or 0)
    precip   = float(daily["precipitation_sum"][0]  or 0)
    snowfall = float(daily["snowfall_sum"][0]        or 0)

    season   = month_to_season(today.month)
    day_time = hour_to_daytime(now.hour)
    mark     = compute_weather_mark(snowfall, precip, temp, season)

    return CurrentWeather(
        date=today.isoformat(),
        temperature_c=round(temp, 1),
        precipitation_mm=round(precip, 1),
        snowfall_cm=round(snowfall, 1),
        season=season,
        day_time=day_time,
        weather_mark=int(mark),
        weather_label=WEATHER_LABEL[mark],
    )
