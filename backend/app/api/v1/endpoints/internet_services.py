"""
Internet Service Management API Endpoints

Provides REST API endpoints for managing Internet services including:
- Internet service creation and configuration
- Tariff plan assignment and management
- Speed and bandwidth configuration
- Service provisioning and activation
- Usage monitoring and analytics
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.internet_service import (
    InternetService, InternetServiceCreate, InternetServiceUpdate,
    InternetServiceList, InternetServiceProvisioningRequest
)
from app.services.internet_service import InternetServiceService
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/customers/{customer_id}/services/internet", 
             response_model=InternetService, 
             status_code=status.HTTP_201_CREATED)
async def create_internet_service(
    customer_id: int,
    service_data: InternetServiceCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new Internet service for a customer."""
    internet_service = InternetServiceService(db)
    
    try:
        # Validate customer exists
        service = internet_service.create_internet_service(customer_id, service_data)
        logger.info(f"Admin {current_admin.username} created Internet service {service.id} for customer {customer_id}")
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Internet service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Internet service"
        )


@router.get("/customers/{customer_id}/services/internet", 
            response_model=InternetServiceList)
async def list_customer_internet_services(
    customer_id: int,
    active_only: bool = Query(True, description="Show only active services"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all Internet services for a specific customer."""
    internet_service = InternetServiceService(db)
    
    try:
        services = internet_service.list_customer_services(customer_id, active_only)
        return InternetServiceList(services=services, total=len(services))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing Internet services for customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Internet services"
        )


@router.get("/services/internet/{service_id}", response_model=InternetService)
async def get_internet_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific Internet service by ID."""
    internet_service = InternetServiceService(db)
    
    try:
        service = internet_service.get_service(service_id)
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving Internet service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Internet service"
        )


@router.put("/services/internet/{service_id}", response_model=InternetService)
async def update_internet_service(
    service_id: int,
    service_data: InternetServiceUpdate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an existing Internet service."""
    internet_service = InternetServiceService(db)
    
    try:
        service = internet_service.update_service(service_id, service_data)
        logger.info(f"Admin {current_admin.username} updated Internet service {service_id}")
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating Internet service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Internet service"
        )


@router.post("/services/internet/{service_id}/provision", 
             response_model=dict)
async def provision_internet_service(
    service_id: int,
    provision_request: InternetServiceProvisioningRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Provision an Internet service (async provisioning queue)."""
    internet_service = InternetServiceService(db)
    
    try:
        result = internet_service.queue_provisioning(service_id, provision_request)
        logger.info(f"Admin {current_admin.username} queued provisioning for Internet service {service_id}")
        return {
            "message": "Provisioning queued successfully",
            "job_id": result.get("job_id"),
            "estimated_completion": result.get("estimated_completion")
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error provisioning Internet service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision Internet service"
        )


@router.post("/services/internet/{service_id}/suspend", response_model=dict)
async def suspend_internet_service(
    service_id: int,
    reason: str = Query(..., description="Reason for suspension"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Suspend an Internet service."""
    internet_service = InternetServiceService(db)
    
    try:
        result = internet_service.suspend_service(service_id, reason, current_admin.id)
        logger.info(f"Admin {current_admin.username} suspended Internet service {service_id}")
        return {"message": "Service suspended successfully", "suspension_id": result.get("suspension_id")}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending Internet service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend Internet service"
        )


@router.post("/services/internet/{service_id}/reactivate", response_model=dict)
async def reactivate_internet_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reactivate a suspended Internet service."""
    internet_service = InternetServiceService(db)
    
    try:
        internet_service.reactivate_service(service_id, current_admin.id)
        logger.info(f"Admin {current_admin.username} reactivated Internet service {service_id}")
        return {"message": "Service reactivated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating Internet service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate Internet service"
        )


@router.get("/services/internet", response_model=InternetServiceList)
async def list_all_internet_services(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tariff_id: Optional[int] = Query(None, description="Filter by tariff plan"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all Internet services with pagination and filtering."""
    internet_service = InternetServiceService(db)
    
    try:
        result = internet_service.list_all_services(
            page=page,
            per_page=per_page,
            status=status,
            tariff_id=tariff_id
        )
        return result
    except Exception as e:
        logger.error(f"Error listing Internet services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Internet services"
        )
