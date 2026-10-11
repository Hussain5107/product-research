from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RootResponse(BaseModel):
    app: str = "ProductHunter AI Backend"
    status: str = "ok"
    region_focus: str = "US"
    next_markets: list[str] = ["UAE", "Saudi Arabia", "Middle East"]


@router.get("/")
async def root() -> RootResponse:
    return RootResponse()
