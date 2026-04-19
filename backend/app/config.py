from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    db_path: Path = Path(__file__).resolve().parent.parent / "tnp_trips.db"

    # Open-Meteo
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    chicago_lat:    float = 41.8781
    chicago_lon:    float = -87.6298
    weather_timeout_s: int = 10

    # CORS Middleware
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
