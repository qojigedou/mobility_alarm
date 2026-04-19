from __future__ import annotations
from enum import IntEnum


class WeatherMark(IntEnum):
    GOOD         = 0
    EXTREME_TEMP = 1
    RAIN         = 2
    SNOW         = 3


WEATHER_LABEL: dict[WeatherMark, str] = {
    WeatherMark.GOOD:         "clear",
    WeatherMark.EXTREME_TEMP: "extreme temperature",
    WeatherMark.RAIN:         "rain",
    WeatherMark.SNOW:         "snow",
}

TEMP_THRESHOLDS: dict[str, float] = {
    "winter": -10.0,
    "spring":   2.0,
    "summer":  32.0,
    "fall":     2.0,
}


def month_to_season(month: int) -> str:
    if month in (12, 1, 2): return "winter"
    if month in (3, 4, 5):  return "spring"
    if month in (6, 7, 8):  return "summer"
    return "fall"


def hour_to_daytime(hour: int) -> str:
    if 5 <= hour < 12:  return "morning"
    if 12 <= hour < 18: return "afternoon"
    return "night"


def compute_weather_mark(
    snowfall_cm: float,
    precip_mm: float,
    temp_c: float,
    season: str,
) -> WeatherMark:
    """
    Ranged priority (highest wins):
      SNOW         -> snowfall > 0
      RAIN         -> precipitation > 0 (no snow)
      EXTREME_TEMP -> temp outside season threshold (no precip)
      GOOD         -> everything within normal range
    """
    if snowfall_cm > 0:
        return WeatherMark.SNOW
    if precip_mm > 0:
        return WeatherMark.RAIN
    if season == "summer" and temp_c > TEMP_THRESHOLDS["summer"]:
        return WeatherMark.EXTREME_TEMP
    if season != "summer" and temp_c < TEMP_THRESHOLDS[season]:
        return WeatherMark.EXTREME_TEMP
    return WeatherMark.GOOD
