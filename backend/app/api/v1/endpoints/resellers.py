"""Stub resellers endpoint to satisfy import during testing."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["resellers"])
async def list_resellers():
    return []
