from __future__ import annotations

import aiohttp
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class DomainSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="DOMAIN_",
        case_sensitive=False,
    )

    # Storage
    db_path: Path = _BACKEND_ROOT / "tnp_trips.db"
    csv_dir: Path = _BACKEND_ROOT / "tnp_csv"

    # Socrata
    socrata_app_token: str = ""
    socrata_base_url:  str = "https://data.cityofchicago.org/resource"
    socrata_select:    str = "trip_start_timestamp,pickup_community_area,fare"

    # Open-Meteo
    weather_archive_url: str   = "https://archive-api.open-meteo.com/v1/archive"
    weather_start:       str   = "2018-11-01"
    chicago_lat:         float = 41.8781
    chicago_lon:         float = -87.6298

    # total=7200 -> 2 h max per large CSV stream; sock_read=300 -> 5 min stall limit
    http_total_timeout:    int = 7200
    http_sockread_timeout: int = 300

    @property
    def http_timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            total=self.http_total_timeout,
            sock_read=self.http_sockread_timeout,
        )

    # Dataset registry
    @property
    def datasets(self) -> dict[str, str]:
        return {
            # "2018_2022": "m6dm-c72p",   # uncomment to include
            "2023_2024": "n26f-ihde",
            # "2025":      "6dvr-xwnh",
        }


domain_settings = DomainSettings()
