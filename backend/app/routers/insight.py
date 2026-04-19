from __future__ import annotations
import aiohttp
import aiosqlite
from fastapi import APIRouter, Depends
from app.dependencies import get_db, get_http
from app.models.schemas import InsightResponse
from app.services.insight_service import build_insight

router = APIRouter(prefix="/api", tags=["insight"])


@router.get("/insight", response_model=InsightResponse)
async def get_insight(
    db:   aiosqlite.Connection   = Depends(get_db),
    http: aiohttp.ClientSession  = Depends(get_http),
):
    return await build_insight(db, http)
