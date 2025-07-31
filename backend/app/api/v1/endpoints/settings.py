"""Stub system settings endpoint for testing."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["settings"])
async def get_settings():
    return {}
