"""
Service Management API Endpoints

Complete tariff module implementation with Internet, Voice, Bundle, 
Recurring services and tariff management endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.exceptions import NotFoundError, DuplicateError
from app.api.dependencies import get_current_admin
from app.models import Administrator
from app.services.services import ServiceManagementService
from app.schemas.services import (
    # Internet Service schemas
    InternetService, InternetServiceCreate, InternetServiceUpdate,
    # Voice Service schemas  
    VoiceService, VoiceServiceCreate, VoiceServiceUpdate,
    # Bundle Service schemas
    BundleService, BundleServiceCreate, BundleServiceUpdate,
    # Recurring Service schemas
    ServiceSearchFilters
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# INTERNET SERVICES ENDPOINTS
# ============================================================================

@router.post("/internet/", response_model=InternetService, status_code=status.HTTP_201_CREATED)
async def create_internet_service(
    service_data: InternetServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new internet service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.create_internet_service(service_data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating internet service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/internet/", response_model=List[InternetService])
async def list_internet_services(
    active_only: bool = Query(True, description="Show only active services"),
    public_only: bool = Query(False, description="Show only public services"),
    min_speed: Optional[int] = Query(None, description="Minimum download speed"),
    max_speed: Optional[int] = Query(None, description="Maximum download speed"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List internet services with optional filters"""
    try:
        service_mgmt = ServiceManagementService(db)
        filters = {}
        if active_only:
            filters["is_active"] = True
        if public_only:
            filters["is_public"] = True
        if min_speed:
            filters["download_speed__gte"] = min_speed
        if max_speed:
            filters["download_speed__lte"] = max_speed
            
        return await service_mgmt.list_internet_services(filters)
    except Exception as e:
        logger.error(f"Error listing internet services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/internet/{service_id}", response_model=InternetService)
async def get_internet_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get internet service by ID"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.get_internet_service(service_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting internet service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/internet/{service_id}", response_model=InternetService)
async def update_internet_service(
    service_id: int,
    service_data: InternetServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update internet service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.update_internet_service(service_id, service_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating internet service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/internet/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internet_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete internet service"""
    try:
        service_mgmt = ServiceManagementService(db)
        success = await service_mgmt.delete_internet_service(service_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete service")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting internet service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# VOICE SERVICES ENDPOINTS
# ============================================================================

@router.post("/voice/", response_model=VoiceService, status_code=status.HTTP_201_CREATED)
async def create_voice_service(
    service_data: VoiceServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new voice service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.create_voice_service(service_data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating voice service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voice/", response_model=List[VoiceService])
async def list_voice_services(
    active_only: bool = Query(True, description="Show only active services"),
    public_only: bool = Query(False, description="Show only public services"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List voice services with optional filters"""
    try:
        service_mgmt = ServiceManagementService(db)
        filters = {}
        if active_only:
            filters["is_active"] = True
        if public_only:
            filters["is_public"] = True
            
        return await service_mgmt.list_voice_services(filters)
    except Exception as e:
        logger.error(f"Error listing voice services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voice/{service_id}", response_model=VoiceService)
async def get_voice_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get voice service by ID"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.get_voice_service(service_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting voice service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/voice/{service_id}", response_model=VoiceService)
async def update_voice_service(
    service_id: int,
    service_data: VoiceServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update voice service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.update_voice_service(service_id, service_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating voice service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/voice/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete voice service"""
    try:
        service_mgmt = ServiceManagementService(db)
        success = await service_mgmt.delete_voice_service(service_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete service")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting voice service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# BUNDLE SERVICES ENDPOINTS
# ============================================================================

@router.post("/bundle/", response_model=BundleService, status_code=status.HTTP_201_CREATED)
async def create_bundle_service(
    service_data: BundleServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new bundle service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.create_bundle_service(service_data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating bundle service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/bundle/", response_model=List[BundleService])
async def list_bundle_services(
    active_only: bool = Query(True, description="Show only active services"),
    public_only: bool = Query(False, description="Show only public services"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """List bundle services with optional filters"""
    try:
        service_mgmt = ServiceManagementService(db)
        filters = {}
        if active_only:
            filters["is_active"] = True
        if public_only:
            filters["is_public"] = True
            
        return await service_mgmt.list_bundle_services(filters)
    except Exception as e:
        logger.error(f"Error listing bundle services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/bundle/{service_id}", response_model=BundleService)
async def get_bundle_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get bundle service by ID"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.get_bundle_service(service_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting bundle service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/bundle/{service_id}", response_model=BundleService)
async def update_bundle_service(
    service_id: int,
    service_data: BundleServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update bundle service"""
    try:
        service_mgmt = ServiceManagementService(db)
        return await service_mgmt.update_bundle_service(service_id, service_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating bundle service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/bundle/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bundle_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Delete bundle service"""
    try:
        service_mgmt = ServiceManagementService(db)
        success = await service_mgmt.delete_bundle_service(service_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete service")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting bundle service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# SERVICE TARIFFS ENDPOINTS
# ============================================================================

# Service Tariff endpoints moved to dedicated tariff module
# Use /api/v1/tariffs/* endpoints for tariff management

# ============================================================================
# UNIFIED SERVICE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/search", response_model=Dict[str, List])
async def search_services(
    search_term: Optional[str] = Query(None, description="Search term"),
    service_type: Optional[str] = Query(None, description="Service type filter"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    is_public: Optional[bool] = Query(None, description="Public status filter"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Search services across all types"""
    try:
        service_mgmt = ServiceManagementService(db)
        filters = ServiceSearchFilters(
            search_term=search_term,
            service_type=service_type,
            is_active=is_active,
            is_public=is_public,
            min_price=min_price,
            max_price=max_price
        )
        return await service_mgmt.search_services(filters)
    except Exception as e:
        logger.error(f"Error searching services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/overview", response_model=Dict[str, Any])
async def get_services_overview(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get services overview and statistics"""
    try:
        service_mgmt = ServiceManagementService(db)
        
        # Get counts for each service type
        internet_count = len(await service_mgmt.list_internet_services({"is_active": True}))
        voice_count = len(await service_mgmt.list_voice_services({"is_active": True}))
        bundle_count = len(await service_mgmt.list_bundle_services({"is_active": True}))
        tariff_count = len(await service_mgmt.list_service_tariffs({"is_active": True}))
        
        return {
            "total_services": internet_count + voice_count + bundle_count,
            "internet_services": internet_count,
            "voice_services": voice_count,
            "bundle_services": bundle_count,
            "active_tariffs": tariff_count,
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Error getting services overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/radius/{service_id}/{service_type}", response_model=Dict[str, Any])
async def get_service_for_radius(
    service_id: int,
    service_type: str,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get service configuration for RADIUS integration"""
    try:
        service_mgmt = ServiceManagementService(db)
        service_config = await service_mgmt.get_service_for_radius(service_id, service_type)
        if not service_config:
            raise HTTPException(status_code=404, detail="Service not found or invalid type")
        return service_config
    except Exception as e:
        logger.error(f"Error getting service for RADIUS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")