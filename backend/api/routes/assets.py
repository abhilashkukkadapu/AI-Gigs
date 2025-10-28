from __future__ import annotations

from fastapi import APIRouter

from backend.videoai.core.storage import list_assets

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("")
async def get_assets():
    return [a.to_dict() for a in list_assets()]
