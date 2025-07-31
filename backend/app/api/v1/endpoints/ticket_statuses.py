import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_admin
from app.core.database import get_db
from app.models import Administrator
from app.schemas.ticket_status import (
    TicketStatus,
    TicketStatusCreate,
    TicketStatusUpdate,
)
from app.services.ticket_status import TicketStatusService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[TicketStatus])
async def list_ticket_statuses(
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all ticket statuses."""
    status_service = TicketStatusService(db)

    try:
        statuses = status_service.list_ticket_statuses(active_only=active_only)
        return statuses
    except Exception as e:
        logger.error(f"Error listing ticket statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving ticket statuses",
        )


@router.post("/", response_model=TicketStatus, status_code=status.HTTP_201_CREATED)
async def create_ticket_status(
    status_data: TicketStatusCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Create a new ticket status."""
    status_service = TicketStatusService(db)

    try:
        ticket_status = status_service.create_ticket_status(status_data)
        logger.info(
            f"Admin {current_admin.username} created ticket status: {ticket_status.code}"
        )
        return ticket_status
    except Exception as e:
        logger.error(f"Error creating ticket status: {e}")
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating ticket status",
        )


@router.get("/{status_id}", response_model=TicketStatus)
async def get_ticket_status(
    status_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Get a specific ticket status by ID."""
    status_service = TicketStatusService(db)

    try:
        ticket_status = status_service.get_ticket_status(status_id)
        return ticket_status
    except Exception as e:
        logger.error(f"Error retrieving ticket status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving ticket status",
        )


@router.put("/{status_id}", response_model=TicketStatus)
async def update_ticket_status(
    status_id: int,
    status_data: TicketStatusUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Update an existing ticket status."""
    status_service = TicketStatusService(db)

    try:
        ticket_status = status_service.update_ticket_status(status_id, status_data)
        logger.info(f"Admin {current_admin.username} updated ticket status {status_id}")
        return ticket_status
    except Exception as e:
        logger.error(f"Error updating ticket status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating ticket status",
        )


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_status(
    status_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Delete a ticket status (only non-system statuses)."""
    status_service = TicketStatusService(db)

    try:
        status_service.delete_ticket_status(status_id)
        logger.info(f"Admin {current_admin.username} deleted ticket status {status_id}")
    except Exception as e:
        logger.error(f"Error deleting ticket status {status_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "system" in str(e) or "cannot be deleted" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif "in use" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting ticket status",
        )


@router.get("/customer-visible/list", response_model=List[TicketStatus])
async def list_customer_visible_statuses(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all customer-visible ticket statuses."""
    status_service = TicketStatusService(db)

    try:
        statuses = status_service.get_customer_visible_statuses()
        return statuses
    except Exception as e:
        logger.error(f"Error listing customer-visible ticket statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer-visible ticket statuses",
        )


@router.get("/final/list", response_model=List[TicketStatus])
async def list_final_statuses(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all final ticket statuses."""
    status_service = TicketStatusService(db)

    try:
        statuses = status_service.get_final_ticket_statuses()
        return statuses
    except Exception as e:
        logger.error(f"Error listing final ticket statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving final ticket statuses",
        )
