"""
Bundle Service Management API Endpoints

Provides REST API endpoints for managing Bundle services including:
- Bundle service creation and configuration
- Combined Internet + Voice + TV packages
- Service provisioning and activation
- Bundle usage monitoring and analytics
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.models.auth import Administrator
from app.schemas.bundle_service import (
    BundleService, BundleServiceCreate, BundleServiceUpdate,
    BundleServiceList, BundleServiceProvisioningRequest
)
from app.services.bundle_service import BundleServiceService
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/customers/{customer_id}/services/bundle", 
             response_model=BundleService, 
             status_code=status.HTTP_201_CREATED)
async def create_bundle_service(
    customer_id: int,
    service_data: BundleServiceCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new Bundle service for a customer."""
    bundle_service = BundleServiceService(db)
    
    try:
        service = bundle_service.create_bundle_service(customer_id, service_data)
        logger.info(f"Admin {current_admin.username} created Bundle service {service.id} for customer {customer_id}")
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Bundle service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Bundle service"
        )


@router.get("/customers/{customer_id}/services/bundle", 
            response_model=BundleServiceList)
async def list_customer_bundle_services(
    customer_id: int,
    active_only: bool = Query(True, description="Show only active services"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all Bundle services for a specific customer."""
    bundle_service = BundleServiceService(db)
    
    try:
        services = bundle_service.list_customer_services(customer_id, active_only)
        return BundleServiceList(services=services, total=len(services))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing Bundle services for customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Bundle services"
        )


@router.get("/services/bundle/{service_id}", response_model=BundleService)
async def get_bundle_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific Bundle service by ID."""
    bundle_service = BundleServiceService(db)
    
    try:
        service = bundle_service.get_service(service_id)
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving Bundle service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Bundle service"
        )


@router.put("/services/bundle/{service_id}", response_model=BundleService)
async def update_bundle_service(
    service_id: int,
    service_data: BundleServiceUpdate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an existing Bundle service."""
    bundle_service = BundleServiceService(db)
    
    try:
        service = bundle_service.update_service(service_id, service_data)
        logger.info(f"Admin {current_admin.username} updated Bundle service {service_id}")
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating Bundle service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Bundle service"
        )


@router.post("/services/bundle/{service_id}/provision", 
             response_model=dict)
async def provision_bundle_service(
    service_id: int,
    provision_request: BundleServiceProvisioningRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Provision a Bundle service (async provisioning queue)."""
    bundle_service = BundleServiceService(db)
    
    try:
        result = bundle_service.queue_provisioning(service_id, provision_request)
        logger.info(f"Admin {current_admin.username} queued provisioning for Bundle service {service_id}")
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
        logger.error(f"Error provisioning Bundle service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision Bundle service"
        )


@router.post("/services/bundle/{service_id}/suspend", response_model=dict)
async def suspend_bundle_service(
    service_id: int,
    reason: str = Query(..., description="Reason for suspension"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Suspend a Bundle service."""
    bundle_service = BundleServiceService(db)
    
    try:
        result = bundle_service.suspend_service(service_id, reason, current_admin.id)
        logger.info(f"Admin {current_admin.username} suspended Bundle service {service_id}")
        return {"message": "Service suspended successfully", "suspension_id": result.get("suspension_id")}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending Bundle service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend Bundle service"
        )


@router.post("/services/bundle/{service_id}/reactivate", response_model=dict)
async def reactivate_bundle_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reactivate a suspended Bundle service."""
    bundle_service = BundleServiceService(db)
    
    try:
        result = bundle_service.reactivate_service(service_id, current_admin.id)
        logger.info(f"Admin {current_admin.username} reactivated Bundle service {service_id}")
        return {"message": "Service reactivated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating Bundle service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate Bundle service"
        )


@router.get("/services/bundle", response_model=BundleServiceList)
async def list_all_bundle_services(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    package_id: Optional[int] = Query(None, description="Filter by bundle package"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all Bundle services with pagination and filtering."""
    bundle_service = BundleServiceService(db)
    
    try:
        result = bundle_service.list_all_services(
            page=page,
            per_page=per_page,
            status=status,
            package_id=package_id
        )
        return result
    except Exception as e:
        logger.error(f"Error listing Bundle services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Bundle services"
        )
