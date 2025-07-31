"""Stub administrators endpoint to satisfy import during testing.

This will be replaced by full implementation later.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["administrators"])
async def list_administrators():
    """Temporary stub returning empty list."""
    return []
