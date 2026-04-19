from __future__ import annotations

import aiohttp
import aiosqlite

from app.tools.data_formatter import WeatherMark
from app.models.schemas import AreaStats, InsightResponse
from app.services.weather_service import fetch_current_weather


async def build_insight(
    db:   aiosqlite.Connection,
    http: aiohttp.ClientSession,
) -> InsightResponse:
    weather  = await fetch_current_weather(http)
    season   = weather.season
    day_time = weather.day_time
    mark     = weather.weather_mark

    # City-wide stats for current weather conditions
    async with db.execute(
        """
        SELECT
            SUM(total_trips) AS total_trips,
            SUM(total_trips * avg_fare_per_trip) / NULLIF(SUM(total_trips), 0) AS wavg_fare
        FROM trips_summary
        WHERE season = ? AND day_time = ? AND weather_mark = ?
        """,
        (season, day_time, mark),
    ) as cur:
        row = await cur.fetchone()

    current_trips = float(row["total_trips"] or 0)
    current_fare  = float(row["wavg_fare"]   or 0)

    # Baseline: same season + day_time but clear weather (mark = 0)
    async with db.execute(
        """
        SELECT
            SUM(total_trips) AS total_trips,
            SUM(total_trips * avg_fare_per_trip) / NULLIF(SUM(total_trips), 0) AS wavg_fare
        FROM trips_summary
        WHERE season = ? AND day_time = ? AND weather_mark = 0
        """,
        (season, day_time),
    ) as cur:
        base = await cur.fetchone()

    good_trips = float(base["total_trips"] or 1)
    good_fare  = float(base["wavg_fare"]   or 0)

    delta_trips_pct = round((current_trips - good_trips) / good_trips * 100, 1)
    delta_fare_pct  = round((current_fare  - good_fare)  / max(good_fare, 0.01) * 100, 1)

    # Top 5 areas by trip volume under current conditions
    async with db.execute(
        """
        SELECT
            pickup_community_area AS area,
            SUM(total_trips) AS area_trips,
            SUM(total_trips * avg_fare_per_trip) / NULLIF(SUM(total_trips), 0) AS area_fare
        FROM trips_summary
        WHERE season = ? AND day_time = ? AND weather_mark = ?
        GROUP BY pickup_community_area
        ORDER BY area_trips DESC
        LIMIT 5
        """,
        (season, day_time, mark),
    ) as cur:
        rows = await cur.fetchall()

    top_areas = [
        AreaStats(
            area=r["area"],
            avg_trips=round(float(r["area_trips"] or 0)),
            avg_fare=round(float(r["area_fare"]   or 0), 2),
        )
        for r in rows
    ]

    headline, reasoning = _compose_message(
        mark=WeatherMark(mark),
        season=season,
        day_time=day_time,
        weather_label=weather.weather_label,
        current_trips=current_trips,
        current_fare=current_fare,
        delta_trips_pct=delta_trips_pct,
        delta_fare_pct=delta_fare_pct,
    )

    return InsightResponse(
        weather=weather,
        headline=headline,
        reasoning=reasoning,
        top_areas=top_areas,
        city_avg_trips=round(current_trips),
        city_avg_fare=round(current_fare, 2),
        good_weather_avg_trips=round(good_trips),
        good_weather_avg_fare=round(good_fare, 2),
        delta_trips_pct=delta_trips_pct,
        delta_fare_pct=delta_fare_pct,
    )


def _compose_message(
    *,
    mark: WeatherMark,
    season: str,
    day_time: str,
    weather_label: str,
    current_trips: float,
    current_fare: float,
    delta_trips_pct: float,
    delta_fare_pct: float,
) -> tuple[str, str]:
    """Pure function - builds headline + reasoning strings. No I/O."""
    direction     = "more"  if delta_trips_pct >= 0 else "fewer"
    fare_direction = "up"   if delta_fare_pct  >= 0 else "down"
    pct_abs       = abs(delta_trips_pct)

    headlines = {
        WeatherMark.SNOW:         f"Snowfall today - expect {direction} rides across the city",
        WeatherMark.RAIN:         "Rain in the forecast - demand tends to rise",
        WeatherMark.EXTREME_TEMP: (
            "Extreme heat today - riders avoid the heat"
            if season == "summer"
            else "Extreme cold today - riders skip the outdoors"
        ),
        WeatherMark.GOOD:         "Clear weather today - normal demand expected",
    }
    headline = headlines[mark]

    reasoning = (
        f"In {season} {day_time}s with {weather_label} conditions, Chicago historically sees "
        f"about {pct_abs:.0f}% {direction} trips compared to clear-weather days. "
        f"Average fare shifts by {abs(delta_fare_pct):.1f}% "
        f"({fare_direction}) to around ${current_fare:.2f}. "
        f"This is based on {int(current_trips):,} historical trip records from 2018–2025."
    )

    return headline, reasoning
