from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.service_type import ServiceTypeService
from app.schemas.service_type import ServiceType, ServiceTypeCreate, ServiceTypeUpdate
from app.api.dependencies import get_current_active_admin
from app.models import Administrator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ServiceType])
async def list_service_types(
    active_only: bool = Query(True, description="Filter by active status"),
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all service types."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_types = service_type_service.list_service_types(active_only=active_only)
        return service_types
    except Exception as e:
        logger.error(f"Error listing service types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service types"
        )


@router.post("/", response_model=ServiceType, status_code=status.HTTP_201_CREATED)
async def create_service_type(
    service_type_data: ServiceTypeCreate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new service type."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_type = service_type_service.create_service_type(service_type_data)
        logger.info(f"Admin {current_admin.username} created service type: {service_type.code}")
        return service_type
    except Exception as e:
        logger.error(f"Error creating service type: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating service type"
        )


@router.get("/{service_type_id}", response_model=ServiceType)
async def get_service_type(
    service_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get a specific service type by ID."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_type = service_type_service.get_service_type(service_type_id)
        return service_type
    except Exception as e:
        logger.error(f"Error retrieving service type {service_type_id}: {e}")
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving service type"
        )


@router.put("/{service_type_id}", response_model=ServiceType)
async def update_service_type(
    service_type_id: int,
    service_type_data: ServiceTypeUpdate,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update an existing service type."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_type = service_type_service.update_service_type(service_type_id, service_type_data)
        logger.info(f"Admin {current_admin.username} updated service type {service_type_id}")
        return service_type
    except Exception as e:
        logger.error(f"Error updating service type {service_type_id}: {e}")
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
            detail="Error updating service type"
        )


@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_type(
    service_type_id: int,
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete a service type (only non-system service types)."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_type_service.delete_service_type(service_type_id)
        logger.info(f"Admin {current_admin.username} deleted service type {service_type_id}")
    except Exception as e:
        logger.error(f"Error deleting service type {service_type_id}: {e}")
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
            detail="Error deleting service type"
        )


@router.get("/recurring/list", response_model=List[ServiceType])
async def list_recurring_service_types(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all recurring service types."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_types = service_type_service.get_recurring_service_types()
        return service_types
    except Exception as e:
        logger.error(f"Error listing recurring service types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving recurring service types"
        )


@router.get("/one-time/list", response_model=List[ServiceType])
async def list_one_time_service_types(
    current_admin: Administrator = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all one-time service types."""
    service_type_service = ServiceTypeService(db)
    
    try:
        service_types = service_type_service.get_one_time_service_types()
        return service_types
    except Exception as e:
        logger.error(f"Error listing one-time service types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving one-time service types"
        )
