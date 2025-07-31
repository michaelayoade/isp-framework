import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_admin
from app.core.database import get_db
from app.models import Administrator
from app.schemas.customer import ContactType, ContactTypeCreate, ContactTypeUpdate
from app.services.contact_type import ContactTypeService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ContactType])
async def list_contact_types(
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all contact types."""
    contact_type_service = ContactTypeService(db)

    try:
        contact_types = contact_type_service.list_contact_types(active_only=active_only)
        return contact_types
    except Exception as e:
        logger.error(f"Error listing contact types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving contact types",
        )


@router.post("/", response_model=ContactType, status_code=status.HTTP_201_CREATED)
async def create_contact_type(
    contact_type_data: ContactTypeCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Create a new contact type."""
    contact_type_service = ContactTypeService(db)

    try:
        contact_type = contact_type_service.create_contact_type(contact_type_data)
        logger.info(
            f"Admin {current_admin.username} created contact type: {contact_type.code}"
        )
        return contact_type
    except Exception as e:
        logger.error(f"Error creating contact type: {e}")
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating contact type",
        )


@router.get("/{contact_type_id}", response_model=ContactType)
async def get_contact_type(
    contact_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Get a specific contact type by ID."""
    contact_type_service = ContactTypeService(db)

    try:
        contact_type = contact_type_service.get_contact_type(contact_type_id)
        return contact_type
    except Exception as e:
        logger.error(f"Error retrieving contact type {contact_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving contact type",
        )


@router.put("/{contact_type_id}", response_model=ContactType)
async def update_contact_type(
    contact_type_id: int,
    contact_type_data: ContactTypeUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Update an existing contact type."""
    contact_type_service = ContactTypeService(db)

    try:
        contact_type = contact_type_service.update_contact_type(
            contact_type_id, contact_type_data
        )
        logger.info(
            f"Admin {current_admin.username} updated contact type {contact_type_id}"
        )
        return contact_type
    except Exception as e:
        logger.error(f"Error updating contact type {contact_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating contact type",
        )


@router.delete("/{contact_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_type(
    contact_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Delete a contact type (only non-system types)."""
    contact_type_service = ContactTypeService(db)

    try:
        contact_type_service.delete_contact_type(contact_type_id)
        logger.info(
            f"Admin {current_admin.username} deleted contact type {contact_type_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting contact type {contact_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "system type" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif "in use" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting contact type",
        )
