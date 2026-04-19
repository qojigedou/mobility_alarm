from __future__ import annotations
from pydantic import BaseModel


class CurrentWeather(BaseModel):
    date:              str
    temperature_c:     float
    precipitation_mm:  float
    snowfall_cm:       float
    season:            str
    day_time:          str
    weather_mark:      int
    weather_label:     str


class AreaStats(BaseModel):
    area:        str
    avg_trips:   float
    avg_fare:    float
    sample_days: int = 0


class InsightResponse(BaseModel):
    weather:                CurrentWeather
    headline:               str
    reasoning:              str
    top_areas:              list[AreaStats]
    city_avg_trips:         float
    city_avg_fare:          float
    good_weather_avg_trips: float
    good_weather_avg_fare:  float
    delta_trips_pct:        float
    delta_fare_pct:         float
