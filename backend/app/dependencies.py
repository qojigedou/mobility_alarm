from __future__ import annotations
import aiohttp
import aiosqlite
from app.state import app_state


async def get_db() -> aiosqlite.Connection:
    return app_state.db


async def get_http() -> aiohttp.ClientSession:
    return app_state.http
