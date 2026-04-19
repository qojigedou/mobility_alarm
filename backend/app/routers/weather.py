from __future__ import annotations
import aiohttp
from fastapi import APIRouter, Depends
from app.dependencies import get_http
from app.models.schemas import CurrentWeather
from app.services.weather_service import fetch_current_weather

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/today", response_model=CurrentWeather)
async def get_today_weather(http: aiohttp.ClientSession = Depends(get_http)):
    return await fetch_current_weather(http)
