from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer_status import CustomerStatusService
from app.schemas.customer_status import CustomerStatus, CustomerStatusCreate, CustomerStatusUpdate
from app.api.dependencies import get_current_active_admin
from app.models import Administrator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CustomerStatus])
async def list_customer_statuses(
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all customer statuses."""
    status_service = CustomerStatusService(db)
    
    try:
        statuses = status_service.list_customer_statuses(active_only=active_only)
        return statuses
    except Exception as e:
        logger.error(f"Error listing customer statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer statuses"
        )


@router.post("/", response_model=CustomerStatus, status_code=status.HTTP_201_CREATED)
async def create_customer_status(
    status_data: CustomerStatusCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new customer status."""
    status_service = CustomerStatusService(db)
    
    try:
        customer_status = status_service.create_customer_status(status_data)
        logger.info(f"Admin {current_admin.username} created customer status: {customer_status.code}")
        return customer_status
    except Exception as e:
        logger.error(f"Error creating customer status: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating customer status"
        )


@router.get("/{status_id}", response_model=CustomerStatus)
async def get_customer_status(
    status_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific customer status by ID."""
    status_service = CustomerStatusService(db)
    
    try:
        customer_status = status_service.get_customer_status(status_id)
        return customer_status
    except Exception as e:
        logger.error(f"Error retrieving customer status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer status"
        )


@router.put("/{status_id}", response_model=CustomerStatus)
async def update_customer_status(
    status_id: int,
    status_data: CustomerStatusUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update an existing customer status."""
    status_service = CustomerStatusService(db)
    
    try:
        customer_status = status_service.update_customer_status(status_id, status_data)
        logger.info(f"Admin {current_admin.username} updated customer status {status_id}")
        return customer_status
    except Exception as e:
        logger.error(f"Error updating customer status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating customer status"
        )


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_status(
    status_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a customer status (only non-system statuses)."""
    status_service = CustomerStatusService(db)
    
    try:
        status_service.delete_customer_status(status_id)
        logger.info(f"Admin {current_admin.username} deleted customer status {status_id}")
    except Exception as e:
        logger.error(f"Error deleting customer status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "system" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        elif "in use" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting customer status"
        )
