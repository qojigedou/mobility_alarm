from __future__ import annotations
import logging
from contextlib import asynccontextmanager

import aiohttp
import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.state import app_state
from app.routers import weather, insight

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.db_path.exists():
        raise RuntimeError(
            f"SQLite database not found at '{settings.db_path}'. "
            "Run fetch_tnp_weather.py first or set DB_PATH in your .env file."
        )

    app_state.db = await aiosqlite.connect(settings.db_path, check_same_thread=False)
    app_state.db.row_factory = aiosqlite.Row

    async with app_state.db.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name='trips_summary'"
    ) as cur:
        if await cur.fetchone() is None:
            await app_state.db.close()
            raise RuntimeError(
                f"Database at '{settings.db_path}' is missing the 'trips_summary' view. "
                "Re-run the ETL script to regenerate it."
            )

    app_state.http = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=settings.weather_timeout_s)
    )
    log.info("DB + HTTP session ready  (db=%s)", settings.db_path)

    yield

    await app_state.db.close()
    await app_state.http.close()
    log.info("DB + HTTP session closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mobility Alarm App",
        version="0.0.1",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(weather.router)
    app.include_router(insight.router)

    @app.get("/health", tags=["ops"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
