import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_admin
from app.core.database import get_db
from app.models import Administrator
from app.schemas.billing_type import BillingType, BillingTypeCreate, BillingTypeUpdate
from app.services.billing_type import BillingTypeService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[BillingType])
async def list_billing_types(
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all billing types."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_types = billing_type_service.list_billing_types(active_only=active_only)
        return billing_types
    except Exception as e:
        logger.error(f"Error listing billing types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving billing types",
        )


@router.post("/", response_model=BillingType, status_code=status.HTTP_201_CREATED)
async def create_billing_type(
    billing_type_data: BillingTypeCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Create a new billing type."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_type = billing_type_service.create_billing_type(billing_type_data)
        logger.info(
            f"Admin {current_admin.username} created billing type: {billing_type.code}"
        )
        return billing_type
    except Exception as e:
        logger.error(f"Error creating billing type: {e}")
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating billing type",
        )


@router.get("/{billing_type_id}", response_model=BillingType)
async def get_billing_type(
    billing_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Get a specific billing type by ID."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_type = billing_type_service.get_billing_type(billing_type_id)
        return billing_type
    except Exception as e:
        logger.error(f"Error retrieving billing type {billing_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving billing type",
        )


@router.put("/{billing_type_id}", response_model=BillingType)
async def update_billing_type(
    billing_type_id: int,
    billing_type_data: BillingTypeUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Update an existing billing type."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_type = billing_type_service.update_billing_type(
            billing_type_id, billing_type_data
        )
        logger.info(
            f"Admin {current_admin.username} updated billing type {billing_type_id}"
        )
        return billing_type
    except Exception as e:
        logger.error(f"Error updating billing type {billing_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating billing type",
        )


@router.delete("/{billing_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing_type(
    billing_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Delete a billing type (only non-system billing types)."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_type_service.delete_billing_type(billing_type_id)
        logger.info(
            f"Admin {current_admin.username} deleted billing type {billing_type_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting billing type {billing_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "system" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif "in use" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting billing type",
        )


@router.get("/recurring/list", response_model=List[BillingType])
async def list_recurring_billing_types(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all recurring billing types."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_types = billing_type_service.get_recurring_billing_types()
        return billing_types
    except Exception as e:
        logger.error(f"Error listing recurring billing types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving recurring billing types",
        )


@router.get("/prepaid/list", response_model=List[BillingType])
async def list_prepaid_billing_types(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all prepaid billing types."""
    billing_type_service = BillingTypeService(db)

    try:
        billing_types = billing_type_service.get_prepaid_billing_types()
        return billing_types
    except Exception as e:
        logger.error(f"Error listing prepaid billing types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving prepaid billing types",
        )
