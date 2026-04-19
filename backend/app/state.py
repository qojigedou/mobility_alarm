from __future__ import annotations
import aiohttp
import aiosqlite


class AppState:
    db:   aiosqlite.Connection
    http: aiohttp.ClientSession


app_state = AppState()
