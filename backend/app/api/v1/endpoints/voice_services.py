"""
Voice Service Management API Endpoints

Provides REST API endpoints for managing Voice services including:
- Voice service creation and configuration
- Phone number assignment and management
- Call plan configuration
- Service provisioning and activation
- Call usage monitoring and analytics
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_admin
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.auth import Administrator
from app.schemas.voice_service import (
    VoiceService,
    VoiceServiceCreate,
    VoiceServiceList,
    VoiceServiceProvisioningRequest,
    VoiceServiceUpdate,
)
from app.services.voice_service import VoiceServiceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/customers/{customer_id}/services/voice",
    response_model=VoiceService,
    status_code=status.HTTP_201_CREATED,
)
async def create_voice_service(
    customer_id: int,
    service_data: VoiceServiceCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new Voice service for a customer."""
    voice_service = VoiceServiceService(db)

    try:
        service = voice_service.create_voice_service(customer_id, service_data)
        logger.info(
            f"Admin {current_admin.username} created Voice service {service.id} for customer {customer_id}"
        )
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Voice service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Voice service",
        )


@router.get("/customers/{customer_id}/services/voice", response_model=VoiceServiceList)
async def list_customer_voice_services(
    customer_id: int,
    active_only: bool = Query(True, description="Show only active services"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all Voice services for a specific customer."""
    voice_service = VoiceServiceService(db)

    try:
        services = voice_service.list_customer_services(customer_id, active_only)
        return VoiceServiceList(services=services, total=len(services))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing Voice services for customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Voice services",
        )


@router.get("/services/voice/{service_id}", response_model=VoiceService)
async def get_voice_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a specific Voice service by ID."""
    voice_service = VoiceServiceService(db)

    try:
        service = voice_service.get_service(service_id)
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving Voice service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Voice service",
        )


@router.put("/services/voice/{service_id}", response_model=VoiceService)
async def update_voice_service(
    service_id: int,
    service_data: VoiceServiceUpdate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update an existing Voice service."""
    voice_service = VoiceServiceService(db)

    try:
        service = voice_service.update_service(service_id, service_data)
        logger.info(
            f"Admin {current_admin.username} updated Voice service {service_id}"
        )
        return service
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating Voice service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Voice service",
        )


@router.post("/services/voice/{service_id}/provision", response_model=dict)
async def provision_voice_service(
    service_id: int,
    provision_request: VoiceServiceProvisioningRequest,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Provision a Voice service (async provisioning queue)."""
    voice_service = VoiceServiceService(db)

    try:
        result = voice_service.queue_provisioning(service_id, provision_request)
        logger.info(
            f"Admin {current_admin.username} queued provisioning for Voice service {service_id}"
        )
        return {
            "message": "Provisioning queued successfully",
            "job_id": result.get("job_id"),
            "estimated_completion": result.get("estimated_completion"),
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error provisioning Voice service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision Voice service",
        )


@router.post("/services/voice/{service_id}/suspend", response_model=dict)
async def suspend_voice_service(
    service_id: int,
    reason: str = Query(..., description="Reason for suspension"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Suspend a Voice service."""
    voice_service = VoiceServiceService(db)

    try:
        result = voice_service.suspend_service(service_id, reason, current_admin.id)
        logger.info(
            f"Admin {current_admin.username} suspended Voice service {service_id}"
        )
        return {
            "message": "Service suspended successfully",
            "suspension_id": result.get("suspension_id"),
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending Voice service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend Voice service",
        )


@router.post("/services/voice/{service_id}/reactivate", response_model=dict)
async def reactivate_voice_service(
    service_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Reactivate a suspended Voice service."""
    voice_service = VoiceServiceService(db)

    try:
        voice_service.reactivate_service(service_id, current_admin.id)
        logger.info(
            f"Admin {current_admin.username} reactivated Voice service {service_id}"
        )
        return {"message": "Service reactivated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating Voice service {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate Voice service",
        )


@router.get("/services/voice", response_model=VoiceServiceList)
async def list_all_voice_services(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    plan_id: Optional[int] = Query(None, description="Filter by call plan"),
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all Voice services with pagination and filtering."""
    voice_service = VoiceServiceService(db)

    try:
        result = voice_service.list_all_services(
            page=page, per_page=per_page, status=status, plan_id=plan_id
        )
        return result
    except Exception as e:
        logger.error(f"Error listing Voice services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Voice services",
        )
